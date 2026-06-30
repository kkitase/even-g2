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
