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

void main()
