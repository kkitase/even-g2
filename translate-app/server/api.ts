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
