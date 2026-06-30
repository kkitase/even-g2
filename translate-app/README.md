# Even G2 Live Translate

[Even Realities G2](https://www.evenrealities.com/smart-glasses) 向けのリアルタイム翻訳プラグイン。
Vite + TypeScript + `@evenrealities/even_hub_sdk` + `@google/genai` 構成。

ブラウザのマイクで拾った**英語**を Web Speech API で認識し、Gemini で**日本語**へ翻訳して
G2 のディスプレイに 1〜2 行で逐次表示する。海外スピーカーの発話を聞きながら訳文を読む用途。

## アーキテクチャ

同じ `src/main.ts` が URL クエリで 2 モードに分岐:
- `http://localhost:5173/` → **capture モード**（Chrome でマイク認識＋翻訳送信）
- `http://localhost:5173/?glass` → **glass モード**（`pnpm sim` がこちらを開く）

```
[Chrome /]  マイク → Web Speech(英語STT) → 確定英文
     │  POST /api/translate { text }
     ▼
[Vite middleware: server/api.ts] → Gemini(gemini-3.5-flash) で日本語訳 → state 更新
     ▲ GET /api/current (1.2s polling)
     │
[evenhub-simulator /?glass] textContainerUpgrade で 1〜2 行を差し替え表示
```

`server/api.ts` は Vite middleware として `/api/translate`（翻訳）と `/api/current`（最新訳文）を提供。
`GEMINI_API_KEY` はサーバー側でしか読まれず、ブラウザには渡らない。

## 前提

- Node.js v20 以上（SDK は v18 非対応）
- pnpm
- `@evenrealities/evenhub-cli` と `@evenrealities/evenhub-simulator` をグローバル install 済み
- 音声認識はブラウザ内蔵 Web Speech API を使うため **Google Chrome** で開く（capture モード）

## セットアップ

```bash
cd translate-app
pnpm install
pnpm rebuild esbuild   # 初回のみ
```

### Gemini API キー

シェル環境変数 `GEMINI_API_KEY` をそのまま使う。未設定なら `.env` を作る:

```bash
cp .env.example .env
# .env を編集して GEMINI_API_KEY=AIza... を記入
```

## 使い方

1. ターミナル 1: `pnpm dev`
2. ターミナル 2: `pnpm sim`（シミュレータ起動、`?glass` 付き URL を開く）
3. Google Chrome で `http://localhost:5173/` を開く → capture UI が出る
4. 「▶ 開始」を押してマイクを許可し、英語を話す（または英語音声を再生する）
5. 区切りごとに日本語訳がシミュレータに 1〜2 行で表示される

## 実機（iPhone + G2）

`pnpm qr` で QR を表示し Even App でスキャン。ただし iOS WebView は Web Speech API
（音声認識）が動かない場合がある。その場合は音声チャンクを Gemini マルチモーダルに
直接投げる方式（仕様書の案B）への差し替えが必要。

## テスト

```bash
pnpm test   # cleanTranslation の単体テスト（vitest）
```

## ハードウェア制約（メモ）

- ディスプレイ: 576×288 px / 眼、4-bit greyscale、組み込みフォントのみ
- 1 ページ最大 4 コンテナ、1 つは必ず `isEventCapture: 1`
- テキスト上限: startup/rebuild 1000 文字、upgrade 2000 文字

## 参考

- 公式 Even Hub Docs: https://hub.evenrealities.com/docs
- SDK npm: https://www.npmjs.com/package/@evenrealities/even_hub_sdk
