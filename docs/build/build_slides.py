"""スマートグラス 3 製品比較スライドを構築する一発スクリプト

ステップ:
1. presentation.xml の sldIdLst を 8 枚に絞る
2. 各 slide{N}.xml のテキストを置換
3. 各 notesSlide{N}.xml にスピーカーノートを埋め込む
"""

from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/kkitase/dev/project/99-eveng2/docs/build/unpacked")
SLIDES_DIR = ROOT / "ppt/slides"
NOTES_DIR = ROOT / "ppt/notesSlides"


def replace_each(path: Path, pairs):
    text = path.read_text(encoding="utf-8")
    queues = defaultdict(list)
    for old, new in pairs:
        queues[old].append(new)
    for old, news in queues.items():
        for new in news:
            idx = text.find(old)
            if idx == -1:
                raise SystemExit(f"NOT FOUND in {path.name}: {old!r}")
            text = text[:idx] + new + text[idx + len(old) :]
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 1. presentation.xml の sldIdLst を絞り込み
# ---------------------------------------------------------------------------
pres_xml = ROOT / "ppt/presentation.xml"
pres_text = pres_xml.read_text(encoding="utf-8")
old_sldidlst_start = pres_text.find("<p:sldIdLst>")
old_sldidlst_end = pres_text.find("</p:sldIdLst>") + len("</p:sldIdLst>")
new_sldidlst = (
    "<p:sldIdLst>\n"
    '    <p:sldId id="257" r:id="rId8"/>\n'   # slide2 Cover
    '    <p:sldId id="263" r:id="rId14"/>\n'  # slide8 3-col
    '    <p:sldId id="268" r:id="rId19"/>\n'  # slide13 Numbered 3 (Meta)
    '    <p:sldId id="270" r:id="rId21"/>\n'  # slide15 Numbered 3 alt (Even)
    '    <p:sldId id="269" r:id="rId20"/>\n'  # slide14 Numbered 5 (Google)
    '    <p:sldId id="276" r:id="rId27"/>\n'  # slide21 Comparison
    '    <p:sldId id="280" r:id="rId31"/>\n'  # slide25 Bullets まとめ
    '    <p:sldId id="294" r:id="rId45"/>\n'  # slide39 Thank you
    "  </p:sldIdLst>"
)
pres_text = pres_text[:old_sldidlst_start] + new_sldidlst + pres_text[old_sldidlst_end:]
pres_xml.write_text(pres_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 2. 各スライドのテキスト置換
# ---------------------------------------------------------------------------

# slide2: カバー
replace_each(
    SLIDES_DIR / "slide2.xml",
    [
        ("Gemini Enterprise で変える", "スマートグラス 3 製品比較"),
        ("企業での AI エージェント活用", "2026 年最新動向ガイド"),
        ("2026-MM-DD", "2026 年 5 月時点"),
        ("グーグル・クラウド・ジャパン合同会社", "Meta Ray-Ban — 撮るグラス"),
        ("マーケティング本部", "Even G2 — 見るグラス"),
        ("Google Cloud 担当部長", "Google (Android XR) — 統合のグラス"),
        ("北瀬 公彦", "カメラ・表示・AI で読み解く"),
        ("AI BUSINESS CONFERENCE 2026 SPRING  in TOKYO", "SMART GLASSES 2026"),
    ],
)


# 共通 Lorem
LOREM_LONG = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna ali. "
LOREM_MEDIUM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magn."


# slide8: 3 製品の基本キャラクター
replace_each(
    SLIDES_DIR / "slide8.xml",
    [
        (LOREM_MEDIUM, "撮るグラス。カメラとスピーカーで写真・音楽・通話・AI 会話までこなします。画面はありません。"),
        (LOREM_MEDIUM, "見るグラス。カメラを省き、レンズのディスプレイに翻訳や通知を文字で映します。"),
        (LOREM_MEDIUM, "統合するグラス。Gemini を搭載し、音声型と表示型の 2 タイプを 2026 年秋から段階的に展開します。"),
        ("<a:t>Lorem</a:t>", "<a:t>3 製品の基本キャラクター</a:t>"),
        ("<a:t> ipsum sit dolor amet</a:t>", "<a:t></a:t>"),
        ("Headline", "Meta Ray-Ban"),
        ("Headline", "Even G2"),
        ("Headline", "Google (Android XR)"),
    ],
)


# slide13: Meta Ray-Ban の 3 つの強み
replace_each(
    SLIDES_DIR / "slide13.xml",
    [
        (LOREM_LONG, "12MP カメラと 3K 動画で、視点そのままのハンズフリー撮影。SNS への投稿もスムーズです。"),
        (LOREM_LONG, "オープンイヤー音響で、音楽・通話・ポッドキャストを再生。Hey Meta と呼びかけて音声操作もできます。"),
        (LOREM_LONG, "Meta AI 連携で景色を認識。夏には日本語を含む 20 言語の翻訳に対応する予定です。"),
        ("Numbered", "Meta Ray-Ban"),
        ("items", "撮る・聴く・話すグラス"),
    ],
)


# slide15: Even G2（タイトル枠なし、01/02/03 横の 3 段落だけ）
# テンプレ構造: 大枠に sz=3000 の段落 3 つ、独立枠に 01/02/03 番号
# 1 行目を「製品名 — 見出し」、2/3 行目を強みのキーワードに
replace_each(
    SLIDES_DIR / "slide15.xml",
    [
        # 段落 2/3（02/03 横）
        ("Lorem ipsum dolor sit amet, consectetur.", "microLED で 3D 表示、35 言語の翻訳字幕に対応"),
        ("Lorem ipsum dolor sit amet, consectetur.", "約 36g・カメラなし、専用リング R1 でタップ操作"),
        # 段落 1（01 横）: 4 フラグメントに分かれた "Lorem ipsum dolor sit amet, consectetur." を統合
        ("<a:t>Lorem i</a:t>", "<a:t>Even G2 — 情報を視界に映すグラス</a:t>"),
        ("<a:t>p</a:t>", "<a:t></a:t>"),
        ("<a:t>sum dolor sit amet, </a:t>", "<a:t></a:t>"),
        ("<a:t>consectetur.</a:t>", "<a:t></a:t>"),
    ],
)


# slide14: Google Android XR の 5 トピック
replace_each(
    SLIDES_DIR / "slide14.xml",
    [
        (LOREM_LONG, "オーディオ型を先行発売。カメラ・マイク・スピーカーを内蔵し、Gemini Live と自然な会話ができます。"),
        (LOREM_LONG, "ディスプレイ型を後続で投入。レンズにナビや翻訳字幕を表示し、視線を上げたまま道案内を受けられます。"),
        (LOREM_LONG, "エージェント機能で、声色を再現した翻訳やコーヒー注文など複数手順の代行が可能です。"),
        (LOREM_LONG, "Android XR と iOS の両対応。Samsung・Qualcomm と共同開発し、49g のプロト試作機より軽量化を予定。"),
        (LOREM_LONG, "発売は 2026 年秋後半から段階展開。ブランドは Warby Parker と Gentle Monster、日本展開と価格は未発表です。"),
        ("Numbered", "Google (Android XR)"),
        ("items", "Gemini 搭載の 2 タイプ展開"),
    ],
)


# slide21: スペック比較（Comparison 4 列）
replace_each(
    SLIDES_DIR / "slide21.xml",
    [
        ("Comparison", "スペック比較"),
        ("Lorem Ipsum", "Meta Ray-Ban"),
        ("Lorem Ipsum", "Even G2"),
        ("Lorem Ipsum", "Google (Android XR)"),
        ("Lorem Ipsum", "観点"),
        ("Bullets should be clear &amp; punchy ", "カメラ 12MP / 3K 動画"),
        ("Single lines when possible", "重量 約 49〜51g、約 6.7 万円〜"),
        ("Bullets should be clear &amp; punchy ", "ディスプレイ microLED 表示"),
        ("Single lines when possible", "重量 約 36g、99,800 円"),
        ("Bullets should be clear &amp; punchy ", "Gemini 搭載、2 タイプ展開"),
        ("Single lines when possible", "2026 年秋以降、日本展開は未発表"),
        ("Bullets should be clear &amp; punchy ", "強み: 撮影 / 表示 / 統合"),
        ("Single lines when possible", "日本販売: 済 / 済 / 未定"),
    ],
)


# slide25: まとめ（6 bullet をすべて 1〜2 行に圧縮）
replace_each(
    SLIDES_DIR / "slide25.xml",
    [
        ("Bullets", "まとめ"),
        ("Bullets should be clear &amp; punchy ", "Meta は外向きのデバイス。カメラとスピーカーで世界を撮る。普及台数は世界 700 万台超"),
        ("Use single lines when possible", "Even は内向きのデバイス。カメラを省き、約 36g で常時着用向きの設計"),
        ("Cover all of your points", "Google は統合のデバイス。Gemini と 2 タイプ展開で両者の長所を取りに行く"),
        ("Use no more than 6-8 bullets", "撮りたい人は Meta、目立たず見たい人は Even、待てる人は Google が向く"),
        ("Don&#x2019;t punctuate bullet points", "判断軸は撮影・表示・デザイン・発売時期の 4 つ"),
        ("Present bullets in logical order", "鍵は Google の秋発売と日本展開"),
    ],
)


# slide39: Thank you はテンプレ既定をそのまま使う


# ---------------------------------------------------------------------------
# Step 3. スピーカーノートを各 notesSlide に埋め込む
# ---------------------------------------------------------------------------

def make_note_para(text: str) -> str:
    return (
        '          <a:p>\n'
        '            <a:pPr indent="0" lvl="0" marL="0" rtl="0" algn="l">\n'
        '              <a:spcBef><a:spcPts val="0"/></a:spcBef>\n'
        '              <a:spcAft><a:spcPts val="0"/></a:spcAft>\n'
        '              <a:buNone/>\n'
        '            </a:pPr>\n'
        '            <a:r>\n'
        '              <a:rPr lang="ja-JP" sz="1200"/>\n'
        f'              <a:t>{text}</a:t>\n'
        '            </a:r>\n'
        '            <a:endParaRPr/>\n'
        '          </a:p>'
    )


def replace_note(notes_file: Path, note_text: str) -> None:
    """notesSlide の空 paragraph をスピーカーノートに置き換える"""
    text = notes_file.read_text(encoding="utf-8")
    # 空のノート placeholder（テンプレ既定の <a:p>...<a:r><a:t/></a:r>...</a:p>）を探す。
    # 既定では <a:t/> という空タグが含まれる段落が 1 つだけある想定。
    empty_run_pattern = "<a:r>\n              <a:t/>\n            </a:r>"
    if empty_run_pattern in text:
        # 空 run を実テキストに差し替え
        replacement = (
            '<a:r>\n              <a:rPr lang="ja-JP" sz="1200"/>\n              <a:t>'
            + note_text
            + "</a:t>\n            </a:r>"
        )
        text = text.replace(empty_run_pattern, replacement, 1)
        notes_file.write_text(text, encoding="utf-8")
    else:
        # フォールバック: <p:txBody> の最後に段落を追加するのではなく、最後の </p:txBody> 前に追加
        marker = "</p:txBody>"
        idx = text.find(marker)
        if idx == -1:
            raise SystemExit(f"no txBody close in {notes_file.name}")
        text = text[:idx] + make_note_para(note_text) + "\n        " + text[idx:]
        notes_file.write_text(text, encoding="utf-8")


NOTES = {
    "notesSlide2.xml": "スマートグラス市場は 2026 年に入って一気に動き出しました。今日は Meta Ray-Ban、Even G2、Google Android XR の 3 製品を、カメラ・表示・AI の軸で比較していきます。所要時間は 10 分ほどです。",
    "notesSlide8.xml": "まず 3 製品の性格をひと言で押さえます。Meta はカメラとスピーカーを積んで撮ったり聴いたりする外向きの設計、Even は逆にカメラを省いて表示と軽さに全振り、Google は両方の機能を Gemini でまとめに来る統合型。発想がまったく違うのがポイントです。",
    "notesSlide13.xml": "Meta Ray-Ban は世界 700 万台超を売った、現状もっとも完成度が高い 1 台です。視点そのままで撮れる 12MP カメラ、オープンイヤー音響、Meta AI による景色認識と翻訳が三本柱。一方で、撮影機能ゆえに公共空間での懸念が出ていて、利用 NG の場所も増えている点には触れておきます。",
    "notesSlide15.xml": "Even G2 はカメラを思い切って捨てた潔さがウリです。レンズ内 microLED で翻訳字幕や通知を視界に映し、見た目はほぼ普通のメガネ。36g 軽量・IP65 防水で常時着用も現実的。一方でタップ操作の安定性は発展途上なので、購入前のレビュー確認は必須と添えます。",
    "notesSlide14.xml": "Google は Android XR と Gemini を引っさげての後発参入。オーディオ型を先行、ディスプレイ型を後続で出す 2 段構えです。声色を再現する翻訳や手順代行のエージェント機能が目玉。発売は 2026 年秋以降で、日本展開や価格はまだ未発表。買えるようになる前にロードマップを押さえておきましょう。",
    "notesSlide21.xml": "スペック比較表でカメラ・表示・重量・価格・発売時期を一望にします。Meta と Even はすでに国内で買える、Google はまだ。軸の優先順位が決まれば、選択肢は自然に絞れます。",
    "notesSlide25.xml": "まとめです。撮りたい人は Meta、目立たず情報を見たい人は Even、機能統合と Gemini を待てる人は Google。判断軸は撮影、翻訳表示、デザイン、発売時期の 4 つに集約されます。今日の話で、自分が一番優先したい軸を 1 つ決めてみてください。",
    "notesSlide39.xml": "ご清聴ありがとうございました。質問やフィードバックがあればぜひ聞かせてください。",
}

for filename, note_text in NOTES.items():
    replace_note(NOTES_DIR / filename, note_text)


print("完了：8 枚のスライド + ノートを更新")
