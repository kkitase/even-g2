/**
 * Gemini の生出力を G2 表示用に正規化する。
 * 前後の空白・引用符を除去し、空行を除いて最大 2 行・80 文字に収める。
 */
export function cleanTranslation(raw: string): string {
  const lines = raw
    .split('\n')
    .map((l) => l.replace(/^[\s"'「『“‘]+/, '').replace(/[\s"'」』”’]+$/, ''))
    .filter((l) => l.length > 0)

  let text = lines.slice(0, 2).join('\n')

  const MAX = 80
  if (text.length > MAX) {
    text = text.slice(0, MAX - 1).trimEnd() + '…'
  }
  return text
}
