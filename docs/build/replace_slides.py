"""各スライドのテキスト置換を順序付きで実行するスクリプト"""

from collections import defaultdict
from pathlib import Path


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


SLIDES_DIR = Path(
    "/Users/kkitase/dev/project/99-eveng2/docs/build/unpacked/ppt/slides"
)


# 共通の Lorem 説明文（slide8 / slide13 / slide14 用）
LOREM_LONG = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna ali. "
LOREM_MEDIUM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magn."


# slide8: 3 製品の基本キャラクター
replace_each(
    SLIDES_DIR / "slide8.xml",
    [
        # 長文の説明を先に 3 つ処理（タイトルの「Lorem」と衝突するため）
        (LOREM_MEDIUM, "撮るグラス。カメラとスピーカーで写真・音楽・通話・AI 会話までこなします。画面はありません。"),
        (LOREM_MEDIUM, "見るグラス。カメラを省き、レンズのディスプレイに翻訳や通知を文字で映します。"),
        (LOREM_MEDIUM, "統合するグラス。Gemini を搭載し、音声型と表示型の 2 タイプを 2026 年秋から段階的に展開します。"),
        # タイトル
        ("<a:t>Lorem</a:t>", "<a:t>3 製品の基本キャラクター</a:t>"),
        ("<a:t> ipsum sit dolor amet</a:t>", "<a:t></a:t>"),
        # Headline 3 つ
        ("Headline", "Meta Ray-Ban"),
        ("Headline", "Even G2"),
        ("Headline", "Google (Android XR)"),
    ],
)


# slide13: Meta Ray-Ban の 3 つの強み
replace_each(
    SLIDES_DIR / "slide13.xml",
    [
        # 説明文を先に
        (LOREM_LONG, "12MP カメラと 3K 動画で、視点そのままのハンズフリー撮影。SNS への投稿もスムーズに行えます。"),
        (LOREM_LONG, "オープンイヤー音響で、音楽・通話・ポッドキャストを再生。Hey Meta と呼びかけて音声操作もできます。"),
        (LOREM_LONG, "Meta AI 連携で景色を認識。夏には日本語を含む 20 言語の翻訳に対応する予定です。重量約 49〜51g、約 6.7 万円〜。"),
        # タイトル
        ("Numbered", "Meta Ray-Ban"),
        ("items", "撮る・聴く・話すグラス"),
    ],
)


# slide15: Even G2 の 3 つの強み
# タイトル文字は <a:t>Lorem i</a:t><a:t>p</a:t><a:t>sum dolor sit amet, </a:t><a:t>consectetur.</a:t> に分割
replace_each(
    SLIDES_DIR / "slide15.xml",
    [
        # 3 項目の説明文（短い Lorem）
        ("Lorem ipsum dolor sit amet, consectetur.", "初代比 75% 拡大の microLED で、3D フローティング表示。表示距離も近・中・遠で切り替えできます。"),
        ("Lorem ipsum dolor sit amet, consectetur.", "35 言語の翻訳字幕に対応。会話の文字起こしと AI 要約、プレゼン原稿表示にも使えます。"),
        ("Lorem ipsum dolor sit amet, consectetur.", "専用リング Even R1 で指先タップ操作。重量約 36g、2 日以上のバッテリー、IP65 防水で常時着用に向きます。"),
        # タイトルは 4 つのフラグメントに分かれている
        ("<a:t>Lorem i</a:t>", "<a:t>Even G2</a:t>"),
        ("<a:t>p</a:t>", "<a:t></a:t>"),
        ("<a:t>sum dolor sit amet, </a:t>", "<a:t></a:t>"),
        ("<a:t>consectetur.</a:t>", "<a:t>情報を視界に映すグラス</a:t>"),
    ],
)


# slide14: Google Android XR の 5 トピック
replace_each(
    SLIDES_DIR / "slide14.xml",
    [
        (LOREM_LONG, "オーディオ型を先行発売。カメラ・マイク・スピーカーを内蔵し、Gemini Live と自然な会話ができます。"),
        (LOREM_LONG, "ディスプレイ型を後続で投入。レンズにナビや翻訳字幕を表示し、視線を上げたまま道案内を受けられます。"),
        (LOREM_LONG, "エージェント機能で、声色を再現した翻訳やコーヒー注文など複数手順の代行が可能です。"),
        (LOREM_LONG, "Android XR と iOS の両対応。Samsung・Qualcomm と共同開発し、49g のプロト試作機より軽量化を予定しています。"),
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
        # Meta 列
        ("Bullets should be clear &amp; punchy ", "カメラ 12MP / 3K 動画"),
        ("Single lines when possible", "重量 約 49〜51g、約 6.7 万円〜"),
        # Even 列
        ("Bullets should be clear &amp; punchy ", "ディスプレイ microLED 表示"),
        ("Single lines when possible", "重量 約 36g、99,800 円"),
        # Google 列
        ("Bullets should be clear &amp; punchy ", "Gemini 搭載、2 タイプ展開"),
        ("Single lines when possible", "2026 年秋以降、日本展開は未発表"),
        # 観点列
        ("Bullets should be clear &amp; punchy ", "強み: 撮影 / 表示 / 統合"),
        ("Single lines when possible", "日本販売: 済 / 済 / 未定"),
    ],
)


# slide25: まとめ
replace_each(
    SLIDES_DIR / "slide25.xml",
    [
        ("Bullets", "まとめ"),
        ("Bullets should be clear &amp; punchy ", "Meta は外向きのデバイス。カメラとスピーカーで世界を撮り、AI に見せる。普及台数は世界 700 万台超。"),
        ("Use single lines when possible", "Even は内向きのデバイス。カメラを捨て、情報表示と軽さに振り切った設計。約 36g で日常使いに向きます。"),
        ("Cover all of your points", "Google は統合するデバイス。Gemini と 2 タイプ展開で両者の長所を取りに行く本命候補。"),
        ("Use no more than 6-8 bullets", "撮りたい人は Meta、目立たず情報を見たい人は Even、Gemini と機能統合を待てる人は Google。"),
        ("Don’t punctuate bullet points", "選ぶ基準は撮影・翻訳表示・デザイン・発売時期の 4 軸。優先順位を決めれば最適解が見えます。"),
        ("Present bullets in logical order", "鍵は Google の秋発売と日本展開。今すぐ買うなら Meta か Even、待てるなら Google も選択肢になります。"),
    ],
)


# slide39: Thank you (touch up)
replace_each(
    SLIDES_DIR / "slide39.xml",
    [],  # 変更なし、デフォルトの「Thank you」を残す
)


print("置換完了")
