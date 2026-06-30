# Even G2 Sample App — AI Prompter

[Even Realities G2](https://www.evenrealities.com/smart-glasses) スマートグラス向けの AI プロンプターサンプル。
Vite + TypeScript + `@evenrealities/even_hub_sdk` + `@google/genai` 構成。

ブラウザに貼り付けたテキストを Gemini で要約し、G2 のディスプレイに 1 ページずつめくり表示する。
登壇のカンペ・記事ブリーフィング・会議メモ整理用途を想定。

`evenhub-simulator` で macOS 上に G2 表示をエミュレートして、実機なしで動作確認できる。

## アーキテクチャ

G2 プラグインは Web アプリ。コードはローカル / 自前サーバーで動き、
iPhone の Even App が WebView でロードし、BLE 経由でグラスへ表示と入力を中継する。
グラス自体ではコードは走らない。

```
              ┌─ POST /api/summarize ─> Gemini ─┐
[Chrome] ─────┤                                  │   SSE
   入力 UI    └─────────── 状態保存 ─────────────┘  /api/stream
                            │
                            ▼
                     [Vite dev server] ──HTTP──> [Even App (WebView)] ──BLE──> [G2 Glasses]
                                        または   [evenhub-simulator (macOS)]
```

同じ `src/main.ts` が URL クエリで 2 モードに分岐:
- `http://localhost:5173/` → **入力 UI モード**（Chrome で開く）
- `http://localhost:5173/?glass` → **グラス描画モード**（`pnpm sim` がこちらを開く）

(SDK の `waitForEvenAppBridge()` は通常 Chrome でも resolve してしまうため、自動判定ではなく URL で明示分岐している)

Vite の middleware (`server/api.ts`) が `/api/summarize` と `/api/stream` (SSE) を提供し、
ブラウザの入力をシミュレータへ即時に流す。

## 前提

- Node.js v20 以上（SDK は v18 非対応）
- pnpm
- `@evenrealities/evenhub-cli` と `@evenrealities/evenhub-simulator` をグローバル install 済み

未インストールなら:

```bash
pnpm setup        # 初回のみ（PNPM_HOME を ~/.zshrc に追記）
source ~/.zshrc   # または新しいターミナルを開く
pnpm add -g @evenrealities/evenhub-cli @evenrealities/evenhub-simulator
```

## セットアップ

```bash
cd sample-app
pnpm install
pnpm rebuild esbuild   # 初回のみ（pnpm の build-script ガード回避）
```

### Gemini API キー

シェル環境変数 `GEMINI_API_KEY` をそのまま使う。未設定の場合のみ `.env` を作る:

```bash
cp .env.example .env
# .env を編集して GEMINI_API_KEY=AIza... を記入
```

`.env` はサーバー側 (`server/api.ts`) でしか読まれない。ブラウザには渡らない。

## 開発

ターミナル 1（Vite dev サーバー）:

```bash
pnpm dev
```

`http://localhost:5173/` で待受。`--host 0.0.0.0` なので同一 LAN の iPhone からも届く。

ターミナル 2（シミュレータ）:

```bash
pnpm sim
```

内部で `evenhub-simulator http://localhost:5173` を呼ぶ。
macOS の GUI ウィンドウが立ち上がり、グラスの表示と入力イベントをエミュレートする。

`src/main.ts` を編集するとホットリロードでシミュレータ側にも反映される。

## 実機（iPhone + G2）で確認

iPhone を同じ LAN に置き、Even App でログイン後:

```bash
pnpm qr
```

QR コードがターミナルに表示されるので Even App でスキャンする。

## ビルド & パッケージ

```bash
pnpm build    # dist/ に本番ビルド
pnpm pack     # dist/ を .ehpk にパッケージ（Even Hub 配布用）
```

## 使い方（AI プロンプター）

1. ターミナル 1: `pnpm dev`
2. ターミナル 2: `pnpm sim` でシミュレータ起動 (内部で `?glass` 付きの URL を開く)
3. Chrome で `http://localhost:5173/` を開く → 入力 UI が出る (クエリなし)
4. 要約したいテキストを貼り付け、スタイル（要点 / 詳細 / 質問）を選んで送信
5. シミュレータに自動でページが流れる（SSE で push）

### スタイル

| 値 | 用途 |
|---|---|
| `summary` | 要点を 1 ページ 1 トピックで（既定） |
| `detail` | 読み上げ用に詳しく整理 |
| `questions` | Q&A 形式で内容を分解 |

### グラス側の操作

| 入力 | 動作 |
|---|---|
| Tap | 次のページ |
| Swipe ↓ | 次のページ |
| Swipe ↑ | 前のページ |
| Double-tap | 最初のページに戻る |

## ファイル構成

```
sample-app/
├── src/
│   └── main.ts         # bridge 有無で glass / browser モードに分岐
├── server/
│   └── api.ts          # Vite middleware: /api/summarize, /api/stream (SSE)
├── app.json            # Even Hub マニフェスト
├── index.html          # WebView / Chrome が読む HTML
├── vite.config.ts      # middleware を Vite に注入
├── tsconfig.json
├── .env.example
└── package.json
```

## ハードウェア制約（メモ）

- ディスプレイ: 576×288 px / 眼、4-bit greyscale（16 階調）、組み込みフォントのみ
- 1 ページにつき最大 4 コンテナ（Text / List / Image）
- 1 つは必ず `isEventCapture: 1`
- テキスト上限: startup/rebuild 1000 文字、upgrade 2000 文字
- 画像サイズ: 幅 20–200 px、高さ 20–100 px

## 参考

- 公式 Even Hub Docs: https://hub.evenrealities.com/docs
- SDK npm: https://www.npmjs.com/package/@evenrealities/even_hub_sdk
- コミュニティ docs（リファレンスアプリも豊富）: https://github.com/nickustinov/even-g2-notes
- 元にしたテンプレ: https://github.com/brianmatzelle/even-realities-g2-glasses
