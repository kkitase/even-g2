# translate-app 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** マイクで拾った英語音声をブラウザで認識し、Gemini API で日本語へ翻訳して Even G2 グラスに 1〜2 行で逐次表示する Web プラグインを作る。

**Architecture:** sample-app と同型。`src/main.ts` が URL クエリで capture モード（`/`、Chrome でマイク認識＋翻訳送信）と glass モード（`/?glass`、SDK でグラス描画）に分岐。`server/api.ts`（Vite middleware）が `/api/translate` で Gemini 翻訳を行い、`/api/current` で最新訳文を返す。glass モードは `/api/current` を 1.2 秒ポーリングして差分表示する。API キーはサーバー側のみで保持。

**Tech Stack:** Vite 7 + TypeScript 5（strict）、`@evenrealities/even_hub_sdk`、`@google/genai`（モデル `gemini-3.5-flash`）、ブラウザ Web Speech API（`SpeechRecognition`）、vitest（純粋ロジックの単体テスト）。

**前提メモ:**
- このプロジェクトは git 管理外。各タスク末尾の「コミット」ステップは **任意**（`git init` 済みの場合のみ実施。ユーザー指示があるまで必須ではない）。
- 作業ディレクトリは `eveng2/translate-app/`（`sample-app/` の姉妹）。コマンドはこのディレクトリ内で実行する。
- 仕様書: `docs/superpowers/specs/2026-06-30-translate-app-design.md`

---

## ファイル構成

| ファイル | 責務 |
|---|---|
| `translate-app/package.json` | 依存・scripts（dev/build/sim/qr/pack/test） |
| `translate-app/tsconfig.json` | strict TypeScript 設定（sample 流用） |
| `translate-app/.gitignore` | node_modules / dist / .env 等 |
| `translate-app/.env.example` | `GEMINI_API_KEY` テンプレート |
| `translate-app/app.json` | Even Hub マニフェスト |
| `translate-app/index.html` | WebView/Chrome が読む HTML（CSS 同梱、`src/main.ts` をロード） |
| `translate-app/src/speech-recognition.d.ts` | Web Speech API の最小型宣言（`any` 回避） |
| `translate-app/src/main.ts` | capture / glass モード分岐と各モード実装 |
| `translate-app/server/clean.ts` | 訳文整形の純粋関数 `cleanTranslation`（単体テスト対象） |
| `translate-app/server/clean.test.ts` | `cleanTranslation` の vitest テスト |
| `translate-app/server/api.ts` | Vite middleware（`/api/translate`, `/api/current`）と Gemini 呼び出し |
| `translate-app/vite.config.ts` | middleware 注入 + env 橋渡し（sample 流用） |
| `translate-app/README.md` | セットアップ・使い方 |

---

## Task 1: プロジェクト雛形と依存インストール

**Files:**
- Create: `translate-app/package.json`
- Create: `translate-app/tsconfig.json`
- Create: `translate-app/.gitignore`
- Create: `translate-app/.env.example`
- Create: `translate-app/app.json`

- [ ] **Step 1: `package.json` を作成**

```json
{
  "name": "eveng2-translate-app",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5173",
    "build": "vite build",
    "sim": "evenhub-simulator http://localhost:5173/?glass",
    "qr": "evenhub qr --http --port 5173",
    "pack": "pnpm run build && evenhub pack app.json dist -o eveng2-translate.ehpk",
    "test": "vitest run"
  },
  "dependencies": {
    "@evenrealities/even_hub_sdk": "^0.0.10",
    "@google/genai": "^2.6.0"
  },
  "devDependencies": {
    "typescript": "^5.9.3",
    "vite": "^7.3.1",
    "vitest": "^3.0.0"
  }
}
```

- [ ] **Step 2: `tsconfig.json` を作成**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

- [ ] **Step 3: `.gitignore` を作成**

```
node_modules
dist
*.ehpk
.DS_Store
.vite
.env
.env.local
```

- [ ] **Step 4: `.env.example` を作成**

```
# Gemini API key (https://aistudio.google.com/apikey)
# .env にコピーして実キーを入れる。ブラウザには露出しないサーバー専用。
GEMINI_API_KEY=
```

- [ ] **Step 5: `app.json` を作成**

```json
{
  "package_id": "com.kkitase.eveng2.translate",
  "name": "Even G2 Live Translate",
  "version": "0.1.0",
  "description": "マイクの英語をリアルタイムに日本語へ翻訳して G2 に表示するプラグイン",
  "author": "kkitase",
  "entrypoint": "index.html"
}
```

- [ ] **Step 6: 依存をインストール**

Run（`translate-app/` 内で）:
```bash
pnpm install
pnpm rebuild esbuild
```
Expected: 依存解決が成功し `node_modules` が生成される。`pnpm rebuild esbuild` は sample-app と同じく build-script ガード回避のため初回のみ。

- [ ] **Step 7: コミット（任意）**

```bash
git add translate-app/package.json translate-app/tsconfig.json translate-app/.gitignore translate-app/.env.example translate-app/app.json
git commit -m "chore: scaffold translate-app project files"
```

---

## Task 2: 訳文整形ロジック `cleanTranslation`（TDD）

Gemini の出力を G2 表示用に正規化する純粋関数。前後の空白・引用符を除去し、空行を除いて最大 2 行・80 文字に収める。

**Files:**
- Create: `translate-app/server/clean.ts`
- Test: `translate-app/server/clean.test.ts`

- [ ] **Step 1: 失敗するテストを書く**

`translate-app/server/clean.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { cleanTranslation } from './clean'

describe('cleanTranslation', () => {
  it('前後の空白を除去する', () => {
    expect(cleanTranslation('  こんにちは  ')).toBe('こんにちは')
  })

  it('前後の引用符を除去する（ASCII と日本語）', () => {
    expect(cleanTranslation('"Hello"')).toBe('Hello')
    expect(cleanTranslation('「こんにちは」')).toBe('こんにちは')
  })

  it('空行を除き最大 2 行に収める', () => {
    expect(cleanTranslation('一行目\n\n二行目\n三行目')).toBe('一行目\n二行目')
  })

  it('80 文字を超えたら末尾を … で詰める', () => {
    const out = cleanTranslation('あ'.repeat(100))
    expect(out.length).toBe(80)
    expect(out.endsWith('…')).toBe(true)
  })

  it('空白のみの入力は空文字を返す', () => {
    expect(cleanTranslation('   ')).toBe('')
  })
})
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run（`translate-app/` 内で）: `pnpm test`
Expected: FAIL（`Failed to resolve import "./clean"` または `cleanTranslation is not a function`）。

- [ ] **Step 3: 最小実装を書く**

`translate-app/server/clean.ts`:
```ts
/**
 * Gemini の生出力を G2 表示用に正規化する。
 * 前後の空白・引用符を除去し、空行を除いて最大 2 行・80 文字に収める。
 */
export function cleanTranslation(raw: string): string {
  const lines = raw
    .split('\n')
    .map((l) => l.replace(/^[\s"'「『“”]+/, '').replace(/[\s"'」』“”]+$/, ''))
    .filter((l) => l.length > 0)

  let text = lines.slice(0, 2).join('\n')

  const MAX = 80
  if (text.length > MAX) {
    text = text.slice(0, MAX - 1).trimEnd() + '…'
  }
  return text
}
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `pnpm test`
Expected: PASS（5 件すべて green）。

- [ ] **Step 5: コミット（任意）**

```bash
git add translate-app/server/clean.ts translate-app/server/clean.test.ts
git commit -m "feat: add cleanTranslation helper with tests"
```

---

## Task 3: サーバー middleware `server/api.ts`

`/api/translate`（POST: 英文 → Gemini 翻訳 → state 更新）と `/api/current`（GET: 最新 state）を提供する。Gemini モデルは `gemini-3.5-flash`。`GEMINI_API_KEY` はサーバー側のみ参照。

**Files:**
- Create: `translate-app/server/api.ts`

- [ ] **Step 1: `server/api.ts` を作成**

```ts
import type { IncomingMessage, ServerResponse } from 'node:http'
import { GoogleGenAI } from '@google/genai'
import { cleanTranslation } from './clean'

const MODEL = 'gemini-3.5-flash'

interface TranslationState {
  version: number
  source: string
  text: string
  createdAt: number
}

let state: TranslationState = {
  version: 0,
  source: '',
  text: '■ Live 翻訳 ■\n\nブラウザで localhost:5173 を開き\n英語を話してください。',
  createdAt: Date.now(),
}

async function readJson<T>(req: IncomingMessage): Promise<T> {
  const chunks: Buffer[] = []
  for await (const chunk of req) chunks.push(chunk as Buffer)
  const raw = Buffer.concat(chunks).toString('utf-8')
  return JSON.parse(raw) as T
}

function send(res: ServerResponse, status: number, body: unknown): void {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.end(JSON.stringify(body))
}

interface TranslateBody {
  text: string
}

async function translate(text: string): Promise<string> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) throw new Error('GEMINI_API_KEY が未設定です。translate-app/.env を確認してください。')

  const ai = new GoogleGenAI({ apiKey })
  const prompt = [
    'あなたは同時通訳者です。入力された英語を、自然で簡潔な日本語に翻訳してください。',
    '- 訳文のみを出力する（説明・原文・引用符・前置きを付けない）',
    '- 1〜2 行、80 文字以内に収める',
    '',
    `英語: ${text}`,
  ].join('\n')

  const response = await ai.models.generateContent({
    model: MODEL,
    contents: prompt,
    config: { temperature: 0.2 },
  })

  return cleanTranslation(response.text ?? '')
}

export async function handleApi(
  req: IncomingMessage,
  res: ServerResponse,
  next: () => void,
): Promise<void> {
  const url = req.url ?? ''

  if (req.method === 'GET' && url === '/api/current') {
    send(res, 200, state)
    return
  }

  if (req.method === 'POST' && url === '/api/translate') {
    try {
      const body = await readJson<TranslateBody>(req)
      const text = (body.text ?? '').trim()
      if (!text) {
        send(res, 400, { error: 'text is required' })
        return
      }
      const translated = await translate(text)
      if (translated) {
        state = {
          version: state.version + 1,
          source: text,
          text: translated,
          createdAt: Date.now(),
        }
      }
      send(res, 200, state)
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      send(res, 500, { error: message })
    }
    return
  }

  next()
}
```

- [ ] **Step 2: コミット（任意）**

```bash
git add translate-app/server/api.ts
git commit -m "feat: add translate/current API middleware"
```

---

## Task 4: `vite.config.ts`（middleware 注入 + env 橋渡し）

**Files:**
- Create: `translate-app/vite.config.ts`

- [ ] **Step 1: `vite.config.ts` を作成**

```ts
import { defineConfig, loadEnv } from 'vite'
import { handleApi } from './server/api'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // server/api.ts は process.env から読むので、ここで橋渡しする
  if (env.GEMINI_API_KEY && !process.env.GEMINI_API_KEY) {
    process.env.GEMINI_API_KEY = env.GEMINI_API_KEY
  }

  return {
    server: {
      host: true,
      port: 5173,
    },
    plugins: [
      {
        name: 'eveng2-translate-api',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            const url = req.url ?? ''
            if (url.startsWith('/api/')) {
              handleApi(req, res, next).catch(next)
              return
            }
            next()
          })
        },
      },
    ],
  }
})
```

- [ ] **Step 2: API が起動することを確認**

Run（ターミナル A、`translate-app/` 内で）: `pnpm dev`
別ターミナル B で:
```bash
curl -s -X POST http://localhost:5173/api/translate -H 'Content-Type: application/json' -d '{"text":""}'
```
Expected: `{"error":"text is required"}`（HTTP 400）。空 body のバリデーションが効いており、middleware が配線されていることを確認。

- [ ] **Step 3: 翻訳が動くことを確認（API キー必須）**

`.env` に実キーを入れた状態で（`cp .env.example .env` 後に編集、または `GEMINI_API_KEY` をシェルに export して `pnpm dev`）、ターミナル B で:
```bash
curl -s -X POST http://localhost:5173/api/translate -H 'Content-Type: application/json' -d '{"text":"Good morning, everyone."}'
```
Expected: `{"version":1,"source":"Good morning, everyone.","text":"おはようございます、皆さん。","createdAt":...}` のような JSON（`text` が日本語訳）。キー未設定なら `{"error":"GEMINI_API_KEY が未設定です。..."}`（HTTP 500）。

- [ ] **Step 4: コミット（任意）**

```bash
git add translate-app/vite.config.ts
git commit -m "feat: wire vite middleware and env bridge"
```

---

## Task 5: `main.ts` — glass モード（SDK 表示 + ポーリング）と分岐

`src/main.ts` を作成し、URL クエリで分岐する。本タスクでは glass モードを実装し、capture モードは次タスクで埋めるための最小プレースホルダにする。Web Speech API の型宣言も用意する。

**Files:**
- Create: `translate-app/src/speech-recognition.d.ts`
- Create: `translate-app/src/main.ts`

- [ ] **Step 1: `src/speech-recognition.d.ts` を作成**

```ts
// Web Speech API は標準 TS DOM lib に含まれないため最小限を宣言する（any 回避）。
interface SpeechRecognitionAlternative {
  readonly transcript: string
  readonly confidence: number
}

interface SpeechRecognitionResult {
  readonly isFinal: boolean
  readonly length: number
  item(index: number): SpeechRecognitionAlternative
}

interface SpeechRecognitionResultList {
  readonly length: number
  item(index: number): SpeechRecognitionResult
}

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number
  readonly results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string
  readonly message: string
}

interface SpeechRecognition extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((ev: SpeechRecognitionEvent) => void) | null
  onerror: ((ev: SpeechRecognitionErrorEvent) => void) | null
  onend: ((ev: Event) => void) | null
  start(): void
  stop(): void
  abort(): void
}

interface SpeechRecognitionStatic {
  new (): SpeechRecognition
}

interface Window {
  SpeechRecognition?: SpeechRecognitionStatic
  webkitSpeechRecognition?: SpeechRecognitionStatic
}
```

- [ ] **Step 2: `src/main.ts` を作成（glass モード実装 + capture プレースホルダ）**

```ts
import {
  waitForEvenAppBridge,
  type EvenAppBridge,
  CreateStartUpPageContainer,
  TextContainerProperty,
  TextContainerUpgrade,
} from '@evenrealities/even_hub_sdk'

// ─── 共有型 ───────────────────────────────────────────────────
interface TranslationState {
  version: number
  source: string
  text: string
  createdAt: number
}

const CONTAINER_ID = 1
const CONTAINER_NAME = 'main'

// ─── エントリ ────────────────────────────────────────────────
// SDK の waitForEvenAppBridge() は Chrome でも resolve しうるため、
// URL クエリ ?glass で明示的に分岐する。シミュレータは ?glass 付きで開く。
async function main(): Promise<void> {
  const isGlass = new URLSearchParams(location.search).has('glass')
  if (isGlass) {
    const bridge = await waitForEvenAppBridge()
    runGlassMode(bridge)
  } else {
    runCaptureMode()
  }
}

// ─── G2 / Simulator 表示モード ───────────────────────────────
function runGlassMode(bridge: EvenAppBridge): void {
  let text = '■ Live 翻訳 ■\n\nブラウザで localhost:5173 を開き\n英語を話してください。'
  let initialized = false
  let lastVersion = -1

  document.body.innerHTML = `
    <main class="glass">
      <h1>Glass Mode（翻訳表示）</h1>
      <p class="hint">この画面はシミュレータの WebView デバッグ表示です。実機 iPhone では非表示。</p>
      <dl class="status">
        <dt>version</dt><dd id="g-version">-</dd>
        <dt>更新</dt><dd id="g-time">-</dd>
      </dl>
      <h2>現在の訳文</h2>
      <pre id="g-current">(loading)</pre>
    </main>
  `

  const $v = document.getElementById('g-version') as HTMLElement
  const $t = document.getElementById('g-time') as HTMLElement
  const $cur = document.getElementById('g-current') as HTMLElement

  const render = async (): Promise<void> => {
    $cur.textContent = text
    const content = text || '(empty)'
    if (!initialized) {
      await bridge.createStartUpPageContainer(
        new CreateStartUpPageContainer({
          containerTotalNum: 1,
          textObject: [
            new TextContainerProperty({
              containerID: CONTAINER_ID,
              containerName: CONTAINER_NAME,
              content,
              xPosition: 20,
              yPosition: 20,
              width: 536,
              height: 248,
              borderWidth: 2,
              borderColor: 10,
              borderRadius: 5,
              paddingLength: 12,
              isEventCapture: 1,
            }),
          ],
        }),
      )
      initialized = true
      return
    }
    await bridge.textContainerUpgrade(
      new TextContainerUpgrade({
        containerID: CONTAINER_ID,
        containerName: CONTAINER_NAME,
        content,
      }),
    )
  }

  void render()

  // dev サーバーの restart/HMR で SSE が切れやすいため、glass 側は polling で堅牢化する。
  const POLL_MS = 1200
  const poll = async (): Promise<void> => {
    try {
      const r = await fetch('/api/current', { cache: 'no-store' })
      if (!r.ok) return
      const next = (await r.json()) as TranslationState
      if (next.version === lastVersion) return
      lastVersion = next.version
      text = next.text
      $v.textContent = String(next.version)
      $t.textContent = next.createdAt ? new Date(next.createdAt).toLocaleTimeString() : '-'
      await render()
    } catch {
      // dev サーバー再起動中など。次の poll を待つ
    }
  }
  setInterval(() => void poll(), POLL_MS)
  void poll()
}

// ─── ブラウザ capture モード（Task 6 で実装） ───────────────
function runCaptureMode(): void {
  document.body.innerHTML = `
    <main class="app">
      <header>
        <h1>Even G2 · Live Translate</h1>
        <p class="hint">(capture モードは Task 6 で実装)</p>
      </header>
    </main>
  `
}

void main()
```

- [ ] **Step 3: glass モードの表示を確認**

ターミナル A: `pnpm dev`、ターミナル B: `pnpm sim`（シミュレータ起動。内部で `?glass` 付き URL を開く）。
ターミナル C で翻訳を 1 件 push:
```bash
curl -s -X POST http://localhost:5173/api/translate -H 'Content-Type: application/json' -d '{"text":"This is a test."}'
```
Expected: 数秒以内にシミュレータのグラス表示が初期メッセージから「これはテストです。」のような日本語訳に差し替わる（最大 1.2 秒のポーリング遅延 + Gemini 応答時間）。WebView デバッグ表示の version が 1 に変わる。

- [ ] **Step 4: コミット（任意）**

```bash
git add translate-app/src/speech-recognition.d.ts translate-app/src/main.ts
git commit -m "feat: implement glass display mode with polling"
```

---

## Task 6: `main.ts` — capture モード（Web Speech + 翻訳送信）

`runCaptureMode()` を本実装に置き換える。Web Speech API で英語を連続認識し、確定（final）した区切りごとに `/api/translate` へ送信。途中経過（interim）と最新訳文を画面表示する。

**Files:**
- Modify: `translate-app/src/main.ts`（`runCaptureMode` 関数を差し替え）

- [ ] **Step 1: `runCaptureMode` を本実装へ置き換える**

`src/main.ts` の `runCaptureMode` 関数（Task 5 のプレースホルダ）を以下に置き換える:
```ts
// ─── ブラウザ capture モード ─────────────────────────────────
function runCaptureMode(): void {
  document.body.innerHTML = `
    <main class="app">
      <header>
        <h1>Even G2 · Live Translate</h1>
        <p class="hint">マイクの英語をリアルタイムに日本語へ翻訳し、G2 グラスに表示します。</p>
      </header>

      <section class="card">
        <div class="actions">
          <button id="toggle">▶ 開始</button>
          <span id="status" class="status">停止中</span>
        </div>

        <label>
          <span class="label">認識中の英語</span>
          <pre id="src" class="box">(マイクを許可して話してください)</pre>
        </label>

        <label>
          <span class="label">最新の日本語訳（G2 表示中）</span>
          <pre id="ja" class="box ja">-</pre>
        </label>
      </section>
    </main>
  `

  const toggle = document.getElementById('toggle') as HTMLButtonElement
  const status = document.getElementById('status') as HTMLSpanElement
  const srcEl = document.getElementById('src') as HTMLElement
  const jaEl = document.getElementById('ja') as HTMLElement

  const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
  if (!Recognition) {
    status.textContent = 'この端末では音声認識を利用できません'
    srcEl.textContent = 'Google Chrome で http://localhost:5173/ を開いてください。'
    toggle.disabled = true
    return
  }

  const rec = new Recognition()
  rec.lang = 'en-US'
  rec.continuous = true
  rec.interimResults = true
  let running = false

  const sendForTranslation = async (raw: string): Promise<void> => {
    const en = raw.trim()
    if (!en) return
    try {
      const r = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: en }),
      })
      const json = (await r.json()) as { text?: string; error?: string }
      if (!r.ok) throw new Error(json.error ?? 'translate failed')
      if (json.text) jaEl.textContent = json.text
    } catch (e) {
      status.textContent = `翻訳エラー: ${e instanceof Error ? e.message : String(e)}`
    }
  }

  rec.onresult = (ev: SpeechRecognitionEvent): void => {
    let interim = ''
    for (let i = ev.resultIndex; i < ev.results.length; i++) {
      const result = ev.results.item(i)
      const transcript = result.item(0).transcript
      if (result.isFinal) {
        void sendForTranslation(transcript)
      } else {
        interim += transcript
      }
    }
    if (interim) srcEl.textContent = interim
  }

  rec.onerror = (ev: SpeechRecognitionErrorEvent): void => {
    // no-speech / aborted は連続認識で頻繁に出るため無視（onend で自動再開）
    if (ev.error !== 'aborted' && ev.error !== 'no-speech') {
      status.textContent = `認識エラー: ${ev.error}`
    }
  }

  rec.onend = (): void => {
    if (running) {
      try {
        rec.start()
      } catch {
        // 連続再起動時の InvalidStateError は無視
      }
    } else {
      status.textContent = '停止中'
    }
  }

  toggle.addEventListener('click', () => {
    if (running) {
      running = false
      rec.stop()
      toggle.textContent = '▶ 開始'
    } else {
      running = true
      try {
        rec.start()
      } catch {
        // already started
      }
      toggle.textContent = '■ 停止'
      status.textContent = '認識中...'
    }
  })
}
```

- [ ] **Step 2: 型チェックが通ることを確認**

Run（`translate-app/` 内で）: `pnpm exec tsc --noEmit -p tsconfig.json`
Expected: エラーなし（出力なしで終了）。`src/` 配下（main.ts と speech-recognition.d.ts）が strict で型エラーなくコンパイルできることを確認。

- [ ] **Step 3: 既存テストが壊れていないことを確認**

Run: `pnpm test`
Expected: PASS（Task 2 の 5 件が引き続き green）。

- [ ] **Step 4: コミット（任意）**

```bash
git add translate-app/src/main.ts
git commit -m "feat: implement capture mode with Web Speech recognition"
```

---

## Task 7: `index.html`・README と結合検証

WebView/Chrome が読む HTML（CSS 同梱）を用意し、エンドツーエンドで動作確認する。

**Files:**
- Create: `translate-app/index.html`
- Create: `translate-app/README.md`

- [ ] **Step 1: `index.html` を作成**

```html
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Even G2 · Live Translate</title>
    <style>
      :root {
        --bg: #0d1117;
        --fg: #e6edf3;
        --muted: #8b949e;
        --accent: #4ade80;
        --card: #161b22;
        --border: #30363d;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", sans-serif;
        background: var(--bg);
        color: var(--fg);
      }
      .app { max-width: 760px; margin: 0 auto; padding: 32px 20px 80px; }
      h1 { font-size: 24px; margin: 0 0 4px; }
      h2 { font-size: 16px; margin: 0 0 12px; color: var(--muted); font-weight: 600; }
      .hint { color: var(--muted); margin: 0 0 24px; font-size: 14px; }
      .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
      label { display: block; margin-bottom: 16px; }
      .label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; }
      .actions { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
      button {
        background: var(--accent);
        color: #052e16;
        border: 0;
        border-radius: 8px;
        padding: 10px 18px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
      }
      button:disabled { opacity: 0.5; cursor: not-allowed; }
      .status { font-size: 13px; color: var(--muted); }
      .box {
        background: var(--bg);
        color: var(--fg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 14px;
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: ui-monospace, SFMono-Regular, monospace;
        font-size: 14px;
        line-height: 1.55;
        min-height: 48px;
      }
      .box.ja { color: var(--accent); border-color: var(--accent); font-size: 18px; }
      .glass { max-width: 720px; margin: 0 auto; padding: 24px 20px 80px; }
      .glass dl.status { display: grid; grid-template-columns: 100px 1fr; gap: 4px 12px; margin: 16px 0 24px; font-family: ui-monospace, monospace; font-size: 13px; }
      .glass dl.status dt { color: var(--muted); }
      .glass pre#g-current { background: #000; color: var(--accent); border: 1px solid var(--accent); border-radius: 8px; padding: 16px; font-family: ui-monospace, monospace; font-size: 18px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; min-height: 120px; }
    </style>
  </head>
  <body>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 2: `README.md` を作成**

````markdown
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
````

- [ ] **Step 3: ビルドが通ることを確認**

Run（`translate-app/` 内で）: `pnpm build`
Expected: `dist/` が生成され成功する（index.html と src バンドル）。エラーなし。

- [ ] **Step 4: エンドツーエンド結合検証（手動）**

`.env` に実 `GEMINI_API_KEY` を設定した状態で:
1. ターミナル 1: `pnpm dev`
2. ターミナル 2: `pnpm sim`
3. Google Chrome で `http://localhost:5173/` を開く → 「Even G2 · Live Translate」UI が表示される
4. 「▶ 開始」→ マイク許可 → 英語音声（例: YouTube の英語動画）を再生
5. 確認:
   - 「認識中の英語」に英文（interim）が流れる
   - 区切りごとに「最新の日本語訳」に日本語が出る
   - 数秒以内にシミュレータのグラス表示が同じ日本語訳に差し替わる
   - Chrome DevTools の Network に `GEMINI_API_KEY` が出ない（`/api/translate` の body は英文のみ）

成功基準（仕様書 §10）をすべて満たすことを確認する。

- [ ] **Step 5: コミット（任意）**

```bash
git add translate-app/index.html translate-app/README.md
git commit -m "feat: add index.html and README, complete translate-app"
```

---

## 自己レビュー結果

- **仕様カバレッジ:** 英→日翻訳（Task 3 prompt）/ ブラウザマイク・Web Speech（Task 6）/ Gemini 翻訳（Task 3）/ G2 1〜2 行表示（Task 5 + clean の 2 行・80 字制限）/ サーバー側 API キー保持（Task 3 + 4）/ シミュレータ確認（Task 5・7）をすべてタスク化済み。仕様 §11 のスコープ外（双方向・iOS STT 保証・履歴永続化）は実装しない。
- **プレースホルダ:** Task 5 の capture モードは「次タスクで実装」と明記した意図的な段階実装で、Task 6 で完全なコードに置換する。それ以外に未確定箇所なし。
- **型整合:** `TranslationState`（version/source/text/createdAt）は main.ts と api.ts で同一形状。`cleanTranslation` のシグネチャは Task 2 で定義し Task 3 で使用。`handleApi` のエンドポイントは `/api/current`・`/api/translate` の 2 つで main.ts のポーリング先・送信先と一致。Web Speech は `.item()` メソッドアクセスで `noUncheckedIndexedAccess` に適合。
