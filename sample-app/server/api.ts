import type { IncomingMessage, ServerResponse } from 'node:http'
import { GoogleGenAI, Type } from '@google/genai'

const MODEL = 'gemini-3.5-flash'
const MAX_PAGES = 10
const PAGE_CHAR_HINT = 'おおむね 1 ページ 100〜140 文字'

interface PromptState {
  version: number
  pages: string[]
  source: string
  style: string
  createdAt: number
}

let state: PromptState = {
  version: 0,
  pages: ['■ AI Prompter ■\n\nブラウザで\nhttp://localhost:5173/\nを開いて要約したいテキストを送ってください。'],
  source: '',
  style: 'summary',
  createdAt: Date.now(),
}

const sseClients = new Set<ServerResponse>()

function broadcast(): void {
  const payload = `data: ${JSON.stringify(state)}\n\n`
  for (const res of sseClients) {
    res.write(payload)
  }
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

interface SummarizeBody {
  text: string
  style?: 'summary' | 'detail' | 'questions'
}

function stylePrompt(style: string): string {
  switch (style) {
    case 'detail':
      return '読み上げ用に詳しく整理する。冗長表現は削るが、固有名詞・数値・人名はそのまま残す。'
    case 'questions':
      return '内容を理解するための質問を 5〜8 個、Q&A 形式で。各 Q が 1 ページ、A は 1〜2 行。'
    case 'summary':
    default:
      return '要点を箇条書きに近い短文で。1 ページ 1 トピック。最初のページに 1 行サマリ。'
  }
}

async function summarize(text: string, style: string): Promise<string[]> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) throw new Error('GEMINI_API_KEY が未設定です。sample-app/.env を確認してください。')

  const ai = new GoogleGenAI({ apiKey })
  const prompt = [
    'あなたは Even Realities G2 スマートグラスへの表示テキストを整える編集者です。',
    'ハードウェア制約:',
    '- ディスプレイは横長で文字情報のみ',
    '- 1 ページ ' + PAGE_CHAR_HINT + '。改行を活用して縦に積む',
    '- 装飾記号は最小限。■ などの 1 文字記号は OK',
    `- 最大 ${MAX_PAGES} ページまで`,
    '',
    `スタイル指示: ${stylePrompt(style)}`,
    '',
    '次の入力テキストを上記制約で再構成し、ページ配列として返してください。',
    '',
    '--- 入力テキストここから ---',
    text,
    '--- 入力テキストここまで ---',
  ].join('\n')

  const response = await ai.models.generateContent({
    model: MODEL,
    contents: prompt,
    config: {
      responseMimeType: 'application/json',
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          pages: {
            type: Type.ARRAY,
            items: { type: Type.STRING },
          },
        },
        required: ['pages'],
      },
      temperature: 0.4,
    },
  })

  const raw = response.text ?? '{"pages":[]}'
  const parsed = JSON.parse(raw) as { pages: string[] }
  const pages = (parsed.pages ?? []).map(p => p.trim()).filter(p => p.length > 0)
  if (pages.length === 0) throw new Error('Gemini が空のページを返しました。')
  return pages.slice(0, MAX_PAGES)
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

  if (req.method === 'GET' && url === '/api/stream') {
    res.statusCode = 200
    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache, no-transform')
    res.setHeader('Connection', 'keep-alive')
    res.write(`data: ${JSON.stringify(state)}\n\n`)
    sseClients.add(res)
    req.on('close', () => sseClients.delete(res))
    return
  }

  if (req.method === 'POST' && url === '/api/summarize') {
    try {
      const body = await readJson<SummarizeBody>(req)
      const text = (body.text ?? '').trim()
      const style = body.style ?? 'summary'
      if (!text) {
        send(res, 400, { error: 'text is required' })
        return
      }
      const pages = await summarize(text, style)
      state = {
        version: state.version + 1,
        pages,
        source: text.slice(0, 200),
        style,
        createdAt: Date.now(),
      }
      broadcast()
      send(res, 200, state)
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      send(res, 500, { error: message })
    }
    return
  }

  next()
}
