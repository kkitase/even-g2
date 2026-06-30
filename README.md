# Even G2 プラグイン集（eveng2）

[Even Realities G2](https://www.evenrealities.com/smart-glasses) スマートグラス向けのプラグイン（Web アプリ）を 2 つ収めたリポジトリです。

- **sample-app**: 貼り付けたテキストを Gemini で要約し、G2 にページめくり表示する「AI プロンプター」
- **translate-app**: マイクの英語をリアルタイムに日本語へ翻訳し、G2 に 1〜2 行表示する「ライブ翻訳」

このページは「Even G2 とは何か」「プラグインはどう作るか」「2 つのアプリの作り方・使い方」をやさしく解説します。BLE プロトコルなど深い技術解説は [`architecture.md`](./architecture.md) を参照してください。

---

## 1. Even G2 とは

ディスプレイ付きのスマートグラスです。視界に文字を重ねて表示する HUD（ヘッドアップディスプレイ）で、次のような特徴があります。

| 項目 | 内容 |
|---|---|
| ディスプレイ | 576×288 px / 眼、4-bit greyscale（16 階調・緑単色）、**組み込みフォントのみ** |
| 入力 | テンプルの**タッチバー**、別売の R1 リング |
| センサー | **マイクあり**（左テンプル）、装着検知 |
| 非搭載 | **カメラなし・スピーカーなし**（プライバシー重視。表示と音声入力で完結） |
| 通信 | iPhone と BLE 5.4 接続（左右テンプルが別々のデバイスとして見える） |

### いちばん大事な前提: コードはグラスでは動かない

プラグインの実体は **Web アプリ（HTML/TypeScript）** です。グラス自体は「表示と入力の端末」にすぎません。

```
[あなたが書くコード(Webアプリ)]
        │ サーバー(開発時=Vite / 配布時=Even Hub)から配信
        ▼
[iPhone の Even App]  ← WebView でアプリをロード
        │ BLE で中継
        ▼
[Even G2 グラス]  ← 文字を表示し、タップ等の入力を返す
```

開発中は iPhone の代わりに **macOS のシミュレータ**（`evenhub-simulator`）でグラス表示を再現できるので、実機がなくても作れます。

---

## 2. プラグインの共通の作り方

2 つのアプリは同じ骨組みでできています。

### 技術スタック

- **Vite + TypeScript**: Web アプリのビルド/開発サーバー
- **`@evenrealities/even_hub_sdk`**: グラスへの描画・入力イベントを扱う公式 SDK
- **`@google/genai`**: Gemini API 呼び出し（要約・翻訳）
- パッケージマネージャは **pnpm**

### SDK でやること（描画の流れ）

1. `waitForEvenAppBridge()` で iPhone(またはシミュレータ)との橋渡しを取得
2. `createStartUpPageContainer()` で初回画面（コンテナ）を作る
3. 以降の更新は `textContainerUpgrade()` で**中身だけ差し替え**（BLE 帯域が細いので全再構築しない）
4. タップ/スワイプ等は `onEvenHubEvent()` で受け取る

ハードウェア制約（SDK が課す上限）:

- 1 ページに最大 4 コンテナ。うち 1 つは必ず `isEventCapture: 1`（入力を受ける）
- テキスト上限: 初期描画 1000 文字 / 更新 2000 文字

### 1 つのコードで「入力UI」と「グラス表示」を切り替える

両アプリとも、同じ `src/main.ts` を **URL クエリ `?glass` の有無**で 2 モードに分岐します。

| URL | モード | 役割 |
|---|---|---|
| `http://localhost:5173/` | ブラウザ入力 / capture | Chrome で開く。入力を受けてサーバーに送る |
| `http://localhost:5173/?glass` | glass | シミュレータ/実機が開く。グラスに描画する |

API キー（`GEMINI_API_KEY`）は **Vite の middleware（`server/api.ts`）= サーバー側でのみ**使い、ブラウザには渡しません。

### 開発と配布の 2 系統

```
開発フロー:  pnpm dev  →  pnpm sim（シミュレータ）/ pnpm qr（実機を QR で）
配布フロー:  pnpm build  →  pnpm pack（.ehpk 生成）→ Even Hub にアップロード
```

`app.json` が配布用マニフェスト（`package_id` / `entrypoint` など）です。

### 共通の前提（初回だけ）

- Node.js **v20 以上**（SDK は v18 非対応）、pnpm
- Even Hub のグローバルツール:

```bash
pnpm add -g @evenrealities/evenhub-cli @evenrealities/evenhub-simulator
```

- Gemini API キー: シェルの `GEMINI_API_KEY` をそのまま使うか、各アプリの `.env` に記入

```bash
cp .env.example .env   # 各アプリ内で
# .env に GEMINI_API_KEY=AIza... を記入
```

---

## 3. Claude Code で開発を加速する（everything-evenhub プラグイン）

上の「共通の作り方」を手で書く代わりに、**公式の Claude Code プラグイン `everything-evenhub`** を使うと、やりたいことを日本語/英語で頼むだけで、Claude が適切な手順（skill）を選んで実行してくれます。Even G2 開発の知識（SDK API・表示制約・シミュレータ・パッケージング等）を 13 個の skill にまとめた公式オープンソースです。

### 導入（Claude Code 内で実行）

```
/plugin marketplace add even-realities/everything-evenhub
/plugin install everything-evenhub@everything-evenhub
/reload-plugins
```

導入後は skill 名を覚える必要はありません。「マイク録音をトグルするボタンを付けて」「実機向けにパッケージして」のように頼めば、Claude が対応する skill を自動で呼びます。

### 入っている skill（13 個）

| skill | 何をするか |
|---|---|
| `quickstart` | Vite + TypeScript + SDK でまっさらな G2 アプリを作る初期セットアップ |
| `template` | evenhub-templates の starter から雛形を生成 |
| `sdk-reference` | `@evenrealities/even_hub_sdk` の API リファレンス |
| `cli-reference` | `evenhub` CLI（login / init / pack / qr 等）のリファレンス |
| `glasses-ui` | G2 の表示制約に沿ったコンテナ・テキスト・画像・リストの UI 構築 |
| `design-guidelines` | G2 向け表示デザインのガイドライン（読みやすさ・レイアウト） |
| `font-measurement` | 組み込みフォントの文字幅計測（折り返し・はみ出し対策） |
| `device-features` | マイク録音・IMU・デバイス情報などハードウェア機能 |
| `handle-input` | タッチパッドのジェスチャー・R1 リング入力・ライフサイクルイベント |
| `background-state` | バックグラウンド復帰時に状態を保持（`setBackgroundState` / `onBackgroundRestore`） |
| `test-with-simulator` | シミュレータでの実行とデバッグ |
| `simulator-automation` | HTTP API でスクリーンショット・入力注入・コンソールログを自動化 |
| `build-and-deploy` | パッケージング（.ehpk）と配布 |

### この 2 アプリで使える例

- translate-app を**バックグラウンド対応**に（背面に回って戻っても状態が消えない）→ `background-state`
- **実機向けにパッケージ＆配布** → `build-and-deploy`
- **タッチ操作を追加**（例: タップで録音トグル、Double Tap を終了に予約）→ `handle-input` + `device-features`
- **表示の折り返し・はみ出しを調整** → `glasses-ui` + `font-measurement`

### 参考リンク

- セットアップ: https://hub.evenrealities.com/docs/AI-tooling/claude%20code/index
- Skill カタログ: https://hub.evenrealities.com/docs/AI-tooling/claude%20code/skill-catalog
- プラグイン（OSS）: https://github.com/even-realities/everything-evenhub

> このほかコミュニティ製（サードパーティ）の連携もあります（例: G2 の音声を外部エージェントへ橋渡しする `even-g2-bridge`、G2 からハンズフリーで Claude Code を操作する `claude-code-g2`）。アプリ本体を作って実機に載せる用途なら、まずは公式の `everything-evenhub` だけで十分です。

---

## 4. sample-app（AI プロンプター）

貼り付けたテキストを Gemini で要約し、G2 に**ページめくり表示**します。登壇のカンペ、記事ブリーフィング、議事録整理などに。

### 仕組み

```
[Chrome /] テキスト貼り付け ──POST /api/summarize──> Gemini で要約(ページ配列)
                                          │
                                          ▼ SSE/polling
[シミュレータ /?glass] 1 ページずつ表示。Tap で次ページ
```

### 使い方

```bash
cd sample-app
pnpm install
pnpm rebuild esbuild   # 初回のみ

# ターミナル1
pnpm dev
# ターミナル2
pnpm sim
# Chrome で http://localhost:5173/ を開く
```

1. スタイル（要点 / 詳細 / 質問 Q&A）を選ぶ
2. テキストを貼り付けて「要約して送信」
3. シミュレータにページが流れる

グラス側の操作: Tap / Swipe↓ = 次ページ、Swipe↑ = 前ページ、Double-tap = 先頭へ。

---

## 5. translate-app（ライブ翻訳）

マイクで拾った**英語**をブラウザの音声認識で文字にし、Gemini で**日本語**へ翻訳して G2 に **1〜2 行**表示します。海外スピーカーを聞きながら訳文を読む用途。

### 仕組み

```
[Chrome /]  マイク → Web Speech(英語認識) → 確定英文
     │  POST /api/translate { text }
     ▼
[server/api.ts] → Gemini(gemini-3.5-flash) で日本語訳 → state 更新
     ▲ GET /api/current (1.2 秒ごとに polling)
     │
[シミュレータ /?glass] textContainerUpgrade で 1〜2 行を差し替え表示
```

ポイント: **「聞く側（capture, `/`）」と「映す側（glass, `?glass`）」が役割分担**しています。翻訳を作るのは capture 側だけで、glass 側はサーバーの最新訳を表示するだけです。

### 使い方（シミュレータで確認）

```bash
cd translate-app
pnpm install
pnpm rebuild esbuild   # 初回のみ

# ターミナル1
pnpm dev
# ターミナル2
pnpm sim
# Google Chrome で http://localhost:5173/ を開く
```

1. 「▶ 開始」を押してマイクを許可
2. 英語を話す（または英語音声を再生）
3. 区切りごとに日本語訳がシミュレータに 1〜2 行で出る

> 音声認識はブラウザ内蔵の Web Speech API を使うため **Google Chrome** で開いてください。

### 実機（iPhone + G2）で使うとき

iPhone の WebView は 1 つの URL しか開けず、iOS では音声認識も動きにくいので、役割を分けます。

1. Mac で `pnpm dev` を起動したまま
2. **Mac の Chrome** で `http://localhost:5173/` を開き「▶ 開始」 ← 聞き役
3. iPhone は `pnpm qr` の QR で `/?glass` を開く ← グラス表示役（Mac と同じ Wi-Fi、QR は Mac の LAN IP）

つまり「発表者の近くに Mac を置いて聞かせ、装着者はグラスで訳を読む」構成です。完全にスマホだけで完結させたい場合は、音声を iPhone で拾って Gemini に直送する別方式（マルチモーダル）への作り替えが必要です。

### テスト

```bash
cd translate-app
pnpm test   # 訳文整形 cleanTranslation の単体テスト（vitest）
```

設計書と実装計画: `docs/superpowers/specs/` と `docs/superpowers/plans/` を参照。

---

## 6. コマンド早見表

各アプリのディレクトリ内で実行します。

| コマンド | 役割 |
|---|---|
| `pnpm install` | 依存をインストール（初回） |
| `pnpm dev` | 開発サーバー起動（必須・常駐） |
| `pnpm sim` | macOS シミュレータでグラス表示を再現 |
| `pnpm qr` | 実機 iPhone 用に QR を表示 |
| `pnpm build` | 本番ビルド（`dist/`） |
| `pnpm pack` | `.ehpk` 配布パッケージを生成 |
| `pnpm test` | テスト（translate-app のみ） |

停止は各ターミナルで `Ctrl + C`。

---

## 7. ディレクトリ構成

```
eveng2/
├── README.md          # 本ドキュメント（やさしい解説）
├── architecture.md    # 深い技術解説（レイヤ構成・BLE・GATT・パケット）
├── docs/              # 資料（pptx、設計書 specs/・実装計画 plans/）
├── sample-app/        # AI プロンプター
└── translate-app/     # ライブ翻訳
    ├── src/main.ts        # ?glass で capture/glass に分岐
    ├── server/api.ts      # /api/translate, /api/current（Gemini 呼び出し）
    ├── server/clean.ts    # 訳文整形（テスト付き）
    ├── vite.config.ts     # middleware 注入
    ├── app.json           # Even Hub マニフェスト
    └── index.html
```

---

## 参考

- 公式 Even Hub Docs: https://hub.evenrealities.com/docs
- SDK npm: https://www.npmjs.com/package/@evenrealities/even_hub_sdk
- コミュニティ docs: https://github.com/nickustinov/even-g2-notes
- BLE プロトコル解析: https://github.com/i-soxi/even-g2-protocol
