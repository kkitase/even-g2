import {
  waitForEvenAppBridge,
  type EvenAppBridge,
  CreateStartUpPageContainer,
  TextContainerProperty,
  TextContainerUpgrade,
  OsEventTypeList,
  type EvenHubEvent,
} from '@evenrealities/even_hub_sdk'

// ─── 共有型 ───────────────────────────────────────────────────
interface PromptState {
  version: number
  pages: string[]
  source: string
  style: 'summary' | 'detail' | 'questions'
  createdAt: number
}

const CONTAINER_ID = 1
const CONTAINER_NAME = 'main'

// ─── エントリ ────────────────────────────────────────────────
// 注: SDK の waitForEvenAppBridge() は通常 Chrome でも resolve するため、
// URL クエリ ?glass で明示的に分岐する。シミュレータ起動時は ?glass 付きで開く。
async function main(): Promise<void> {
  const isGlass = new URLSearchParams(location.search).has('glass')
  if (isGlass) {
    const bridge = await waitForEvenAppBridge()
    runGlassMode(bridge)
  } else {
    runBrowserMode()
  }
}

// ─── G2 / Simulator 表示モード ───────────────────────────────
function runGlassMode(bridge: EvenAppBridge): void {
  let pages: string[] = ['■ AI Prompter ■\n\nブラウザで\nlocalhost:5173 を開いて\nテキストを送ってください。']
  let pageIndex = 0
  let initialized = false
  let lastVersion = -1
  let lastStyle = '-'

  // デモ時に「今グラスに何が出ているか」を WebView 側にも表示
  document.body.innerHTML = `
    <main class="glass">
      <h1>Glass Mode</h1>
      <p class="hint">この画面はシミュレータの WebView デバッグ表示です。実機 iPhone では非表示。</p>
      <dl class="status">
        <dt>version</dt><dd id="g-version">-</dd>
        <dt>style</dt><dd id="g-style">-</dd>
        <dt>page</dt><dd id="g-page">-</dd>
      </dl>
      <h2>現在ページ</h2>
      <pre id="g-current">(loading)</pre>
    </main>
  `

  const $v = document.getElementById('g-version') as HTMLElement
  const $s = document.getElementById('g-style') as HTMLElement
  const $p = document.getElementById('g-page') as HTMLElement
  const $cur = document.getElementById('g-current') as HTMLElement

  const refreshStatus = (): void => {
    $v.textContent = String(lastVersion)
    $s.textContent = lastStyle
    $p.textContent = `${pageIndex + 1} / ${pages.length}`
    $cur.textContent = pages[pageIndex] ?? ''
  }

  const render = async (): Promise<void> => {
    refreshStatus()
    const content = pages[pageIndex] ?? '(empty)'
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

  const handleEvent = (event: EvenHubEvent): void => {
    const t = event.textEvent?.eventType ?? event.sysEvent?.eventType ?? event.listEvent?.eventType
    switch (t) {
      case OsEventTypeList.CLICK_EVENT:
      case undefined:
      case OsEventTypeList.SCROLL_BOTTOM_EVENT:
        pageIndex = (pageIndex + 1) % pages.length
        void render()
        break
      case OsEventTypeList.SCROLL_TOP_EVENT:
        pageIndex = (pageIndex - 1 + pages.length) % pages.length
        void render()
        break
      case OsEventTypeList.DOUBLE_CLICK_EVENT:
        pageIndex = 0
        void render()
        break
    }
  }

  bridge.onEvenHubEvent(handleEvent)
  void render()

  // dev サーバーの restart/HMR で SSE が切れやすいので、シミュレータ側は polling で堅牢化
  const POLL_MS = 1500
  const poll = async (): Promise<void> => {
    try {
      const r = await fetch('/api/current', { cache: 'no-store' })
      if (!r.ok) return
      const next = (await r.json()) as PromptState
      if (next.version === lastVersion) return
      lastVersion = next.version
      lastStyle = next.style
      pages = next.pages
      pageIndex = 0
      await render()
    } catch {
      // dev サーバー再起動中など。次の poll を待つ
    }
  }
  setInterval(() => void poll(), POLL_MS)
  void poll()
}

// ─── ブラウザ入力モード ─────────────────────────────────────
function runBrowserMode(): void {
  document.body.innerHTML = `
    <main class="app">
      <header>
        <h1>Even G2 · AI Prompter</h1>
        <p class="hint">テキストを Gemini で要約して、G2 グラスにページめくり表示します。</p>
      </header>

      <section class="card">
        <label>
          <span class="label">スタイル</span>
          <select id="style">
            <option value="summary">要点 (summary)</option>
            <option value="detail">詳細 (detail)</option>
            <option value="questions">質問 Q&amp;A (questions)</option>
          </select>
        </label>

        <label>
          <span class="label">テキスト</span>
          <textarea id="text" rows="10" placeholder="ここに記事・議事録・スクリプトなどを貼り付け..."></textarea>
        </label>

        <div class="actions">
          <button id="submit">要約して送信</button>
          <span id="status" class="status"></span>
        </div>
      </section>

      <section class="card">
        <h2>現在 G2 に表示中</h2>
        <div id="meta" class="meta"></div>
        <ol id="pages" class="pages"></ol>
      </section>
    </main>
  `

  const style = document.getElementById('style') as HTMLSelectElement
  const text = document.getElementById('text') as HTMLTextAreaElement
  const submit = document.getElementById('submit') as HTMLButtonElement
  const status = document.getElementById('status') as HTMLSpanElement
  const meta = document.getElementById('meta') as HTMLDivElement
  const pagesEl = document.getElementById('pages') as HTMLOListElement

  const renderState = (s: PromptState): void => {
    meta.textContent = s.version === 0
      ? '(まだ送信されていません)'
      : `v${s.version} · style=${s.style} · ${new Date(s.createdAt).toLocaleTimeString()}`
    pagesEl.innerHTML = ''
    for (const p of s.pages) {
      const li = document.createElement('li')
      li.textContent = p
      pagesEl.appendChild(li)
    }
  }

  submit.addEventListener('click', async () => {
    const body = text.value.trim()
    if (!body) {
      status.textContent = 'テキストを入力してください'
      return
    }
    submit.disabled = true
    status.textContent = 'Gemini に問い合わせ中...'
    try {
      const r = await fetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: body, style: style.value }),
      })
      const json = await r.json()
      if (!r.ok) throw new Error(json.error ?? 'unknown error')
      renderState(json as PromptState)
      status.textContent = '送信しました'
    } catch (e) {
      status.textContent = `エラー: ${e instanceof Error ? e.message : String(e)}`
    } finally {
      submit.disabled = false
    }
  })

  // 現状取得 + SSE 購読でリアルタイム反映
  const es = new EventSource('/api/stream')
  es.onmessage = (ev) => renderState(JSON.parse(ev.data) as PromptState)
}

void main()
