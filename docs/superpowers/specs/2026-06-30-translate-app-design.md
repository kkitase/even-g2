# translate-app 設計仕様

- 日付: 2026-06-30
- 対象: Even Realities G2 スマートグラス向けプラグイン（Web アプリ）
- 保存先: `eveng2/translate-app/`（`sample-app/` の姉妹アプリ）

## 1. 目的

マイクで拾った**英語音声**をリアルタイムに聞き取り、Gemini API で**日本語**へ翻訳し、訳文を G2 のディスプレイに **1〜2 行**で逐次表示する。海外スピーカーの発話を聞きながらグラス上で日本語訳を読む用途を想定。

## 2. 前提・制約

- プラグインの JS/TS はグラスでは動かない。Web アプリとして Vite から配信され、Chrome（開発）/ Even App の WebView（実機）/ evenhub-simulator（macOS）がロードする。グラスとの通信は Even App が BLE で中継する。
- ディスプレイ: 576×288 px / 眼、4-bit greyscale、組み込みフォントのみ。1 ページ最大 4 コンテナ、1 つは必ず `isEventCapture: 1`。テキスト上限 startup/rebuild 1000 字・upgrade 2000 字。
- 公式 Hub SDK（`@evenrealities/even_hub_sdk`）は実機マイクの音声ストリームを公開していない。よって音声入力は**ブラウザ（PC/スマホ）のマイク**を用いる。案A では Web Speech API がマイク取得を内部で管理するため、明示的な `getUserMedia` 呼び出しは不要（ブラウザがマイク許可を求める）。案Bへ切り替える場合は `getUserMedia` + `MediaRecorder` を使う。
- 実行環境の主対象は **macOS シミュレータ**（= Mac の Chrome 経由）。

## 3. 採用方針（案A）

**ブラウザ音声認識でセグメント区切り → Gemini でテキスト翻訳。**

- Chrome ページが Web Speech API（`SpeechRecognition`、言語 `en-US`）で英語を連続認識し、文の区切り（final 結果）ごとに英文を確定する。
- 確定英文を `/api/translate` に POST → サーバーが Gemini（`gemini-3.5-flash`）で日本語訳 → SSE（`/api/stream`）でグラス描画側へ push する。
- STT はブラウザ内蔵のため、Gemini 呼び出しは翻訳のみ。最も低遅延・低コスト・実装が薄い。

### 不採用案（記録）

- **案B（数秒チャンク録音 → Gemini マルチモーダルで音声→訳を一括）**: ブラウザ STT 非依存で iOS 実機でも動くが、遅延・コストが大きく文が割れやすい。将来 iOS 実機対応が必要になった際のフォールバックとして残す。
- **案C（Gemini Live API ストリーミング）**: 最低遅延だが WebSocket 認証など構成が複雑。「数秒OK・シンプル」要件に合わないため除外。

### 既知の制約

- Web Speech API は実質 Chrome 前提。シミュレータ運用（Mac の Chrome 経由）では問題ないが、iOS 実機の WebView では STT が動かない可能性がある。その場合は案Bへ差し替える。

## 4. データフロー

```
[Chrome /]  マイク → Web Speech(英語STT) → 確定英文
     │  POST /api/translate { text }
     ▼
[Vite middleware: server/api.ts] → Gemini(gemini-3.5-flash) で日本語訳
     │  訳文を SSE (/api/stream) へ push
     ▼
[evenhub-simulator /?glass] textContainerUpgrade で 1〜2 行を差し替え表示
```

同じ `src/main.ts` が URL クエリで 2 モードに分岐する（sample-app と同方式）:

- `http://localhost:5173/` → **capture モード**（Chrome で開く。マイク取得＋STT＋翻訳送信）
- `http://localhost:5173/?glass` → **glass モード**（`pnpm sim` がこちらを開く。SSE 購読＋表示）

## 5. ファイル構成

```
translate-app/
├── src/main.ts        # URLクエリで capture(/) と glass(/?glass) に分岐
├── server/api.ts      # /api/translate (POST→Gemini→SSE push), /api/stream (SSE)
├── app.json           # Even Hub マニフェスト (package_id: com.kkitase.eveng2.translate)
├── index.html         # WebView / Chrome が読む HTML（main.ts をロード）
├── vite.config.ts     # server/api.ts の middleware を Vite に注入
├── tsconfig.json
├── .env.example       # GEMINI_API_KEY=...
├── .gitignore
├── package.json       # scripts: dev / build / sim / qr / pack
└── README.md
```

`package.json` の scripts と依存は sample-app を踏襲する:

- 依存: `@evenrealities/even_hub_sdk`, `@google/genai`
- devDeps: `typescript`, `vite`
- scripts: `dev`（`vite --host 0.0.0.0 --port 5173`）/ `build` / `sim`（`evenhub-simulator http://localhost:5173/?glass`）/ `qr` / `pack`

## 6. コンポーネント責務

### capture モード（`src/main.ts` の `/` 分岐）

- `SpeechRecognition`（`webkitSpeechRecognition` フォールバック）を `lang='en-US'`, `continuous=true`, `interimResults=true` で起動。
- `onresult`: final な結果が出た区切りごとに、その英文を `/api/translate` へ POST。interim（途中経過）は送らない（コストと表示ちらつき回避）。
- `onend`: 自動で `start()` を呼び直す（ブラウザが無音などで止めるため）。
- マイク不許可・`SpeechRecognition` 非対応・`network`/`no-speech` エラーは画面に簡易メッセージ表示。
- 画面 UI は最小限: 開始/停止ボタン、認識中の英文（interim 含む）と直近の日本語訳のプレビュー。

### glass モード（`src/main.ts` の `/?glass` 分岐）

- `waitForEvenAppBridge()` → `createStartUpPageContainer()` で空（またはプレースホルダ）ページを 1 コンテナ・`isEventCapture: 1` で生成。
- `/api/stream` を `EventSource` で購読。訳文を受信するたび `textContainerUpgrade()` で内容を差し替え（最新の訳文 1 件を最大 2 行）。
- 入力イベントは最小構成。まずは表示のみ。任意で Tap → 一時停止/再開トグルを後付け可能（初期実装では必須ではない）。

### server/api.ts（Vite middleware）

- `POST /api/translate`: body の `{ text }`（英文）を受け取り、Gemini（`@google/genai`、モデル `gemini-3.5-flash`）へ「英語を自然な日本語に訳す。訳文のみを出力。1〜2 行・80 字以内」の指示で投げる。結果（日本語訳）を SSE 経由で glass クライアントへ push し、HTTP レスポンスでも訳文を返す（capture 側のプレビュー用）。
- `GET /api/stream`: SSE エンドポイント。接続中の glass クライアントを保持し、訳文を push する。
- `GEMINI_API_KEY` はサーバー側（`process.env` / `.env`）のみで参照し、ブラウザには渡さない。

## 7. 表示仕様（G2）

- 1 コンテナ・`isEventCapture: 1`。
- 最新の訳文 1 件を表示。1〜2 行に収まらない長文は折り返し（または末尾優先で切り詰め）。upgrade 上限 2000 字内で運用上問題なし。
- 4-bit greyscale・組み込みフォント前提なので装飾は行わずプレーンテキストのみ。

## 8. 翻訳プロンプト方針

- システム/指示: 「あなたは同時通訳者。入力された英語を自然で簡潔な日本語に訳す。訳文のみを出力し、説明・原文・引用符を付けない。1〜2 行、80 字以内に収める。」
- 入力: 確定英文 1 区切り。
- 出力: 日本語訳テキストのみ。

## 9. エラー処理

| 事象 | 対処 |
|---|---|
| マイク不許可 | capture UI にエラー表示。再許可を促す |
| `SpeechRecognition` 非対応ブラウザ | capture UI に「Chrome で開いてください」を表示 |
| Web Speech `onend` / `no-speech` / `network` | `start()` を自動リトライ（指数バックオフ不要、即再開） |
| Gemini 呼び出し失敗 | その区切りをスキップし前の表示を維持。サーバーコンソールに警告ログ |
| `waitForEvenAppBridge()` が返らない | sample-app と同じ既知事象。`--host 0.0.0.0` 起動と URL を確認 |

## 10. 成功基準（検証可能）

1. `pnpm dev` + `pnpm sim` 後、Chrome で `/` を開きマイクを許可 → 英語音声（例: YouTube）を流すと、数秒以内にシミュレータへ日本語訳が 1〜2 行で表示される。
2. 続けて話すと、区切りごとに訳文が差し替わる。
3. ブラウザの通信に `GEMINI_API_KEY` が現れない（サーバー側のみで保持）。
4. `pnpm dev` / `pnpm sim` の操作感が sample-app と同一。

## 11. スコープ外（YAGNI）

- 双方向（日→英）翻訳の切替 UI。
- iOS 実機での STT 動作保証（案Bフォールバックは将来課題）。
- 訳文履歴の永続化・スクロール UI。
- 話者分離・言語自動判定（入力は英語固定）。
