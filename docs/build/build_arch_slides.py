"""architecture.md の内容を既存テンプレートに差し込んで architecture.pptx を作成する。

ソース pptx をテンポラリディレクトリへ展開し、各スライド XML のテキストを
順序付きで置換してから再パッケージする。replace_slides.py と同じ
find-first 戦略で重複文字列も扱う。
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

SRC_PPTX = Path(
    "/Users/kkitase/dev/project/99-eveng2/docs/スマートグラス3製品比較-slide.pptx"
)
OUT_PPTX = Path("/Users/kkitase/dev/project/99-eveng2/docs/architecture.pptx")


def replace_each(path: Path, pairs: list[tuple[str, str]]) -> None:
    """同じ old が複数回現れる場合は出現順に new を割り当てる。"""
    text = path.read_text(encoding="utf-8")
    queues: dict[str, list[str]] = defaultdict(list)
    for old, new in pairs:
        queues[old].append(new)
    for old, news in queues.items():
        for new in news:
            idx = text.find(old)
            if idx == -1:
                raise SystemExit(f"NOT FOUND in {path.name}: {old!r}")
            text = text[: idx] + new + text[idx + len(old) :]
    path.write_text(text, encoding="utf-8")


# ============================================================
# スライドごとの置換定義
# ============================================================

# 1. タイトル
SLIDE2 = [
    ("スマートグラス 3 製品比較", "Even G2 アーキテクチャ解説"),
    ("2026 年最新動向ガイド", "プラグインから物理ピクセルまで"),
    ("2026 年 5 月時点", "2026 年 5 月版"),
    ("Meta Ray-Ban — 撮るグラス", "第 1 部 — プラグイン開発者の視点"),
    ("Even G2 — 見るグラス", "第 2 部 — 実機 BLE プロトコルの実体"),
    ("Google (Android XR) — 統合のグラス", "全スタックを 8 枚で俯瞰する"),
    ("カメラ・表示・AI で読み解く", "Web → iPhone → BLE → micro-LED"),
    ("SMART GLASSES 2026", "EVEN G2 ARCHITECTURE"),
]

# 2. 全体像 3-column
SLIDE8 = [
    # 説明文を先に処理（タイトル "Meta Ray-Ban" 等が見出しと重複するため）
    (
        "撮るグラス。カメラとスピーカーで写真・音楽・通話・AI 会話までこなします。画面はありません。",
        "Vite で配信される Web アプリ。SDK 経由でページを定義し、"
        "入力イベントに反応する。コードはサーバ／開発マシン側で実行。",
    ),
    (
        "見るグラス。カメラを省き、レンズのディスプレイに翻訳や通知を文字で映します。",
        "WebView でプラグインをホストし、JS Bridge ↔ BLE Central を担当。"
        "左右テンプルへ 2 本の BLE 接続を張る。",
    ),
    (
        "統合するグラス。Gemini を搭載し、音声型と表示型の 2 タイプを 2026 年秋から段階的に展開します。",
        "BLE 5.4 + PAwR で通信。左右テンプルは独立 MCU、"
        "ディスプレイのみ FPC で物理同期（HAO 設計）。",
    ),
    ("3 製品の基本キャラクター", "全体像 — コードはどこで走るか"),
    ("Meta Ray-Ban", "Web アプリ層"),
    ("Even G2", "iPhone Even App 層"),
    ("Google (Android XR)", "Even G2 グラス層"),
]

# 3. プラグイン側 3 ステップ
SLIDE13 = [
    ("Meta Ray-Ban", "プラグイン側"),
    ("撮る・聴く・話すグラス", "初期化 → 初回描画 → 差分更新"),
    (
        "12MP カメラと 3K 動画で、視点そのままのハンズフリー撮影。SNS への投稿もスムーズです。",
        "Bridge 確立。waitForEvenAppBridge() で Even App ↔ Web の接続を待ち、"
        "onEvenHubEvent() で入力イベントを購読する。",
    ),
    (
        "オープンイヤー音響で、音楽・通話・ポッドキャストを再生。Hey Meta と呼びかけて音声操作もできます。",
        "初回描画。createStartUpPageContainer() でテキストコンテナを 1 ページ構築。"
        "1 つは isEventCapture:1 が必須（入力受け取り）。",
    ),
    (
        "Meta AI 連携で景色を認識。夏には日本語を含む 20 言語の翻訳に対応する予定です。",
        "差分更新。Tap / Swipe 等で pageIndex を更新し、"
        "textContainerUpgrade() で中身だけ書き換える。BLE 帯域節約。",
    ),
]

# 4. ハードウェア 3 つの設計判断
SLIDE15 = [
    ("Even G2 — 情報を視界に映すグラス", "ハードウェアの 3 つの設計判断"),
    (
        "microLED で 3D 表示、35 言語の翻訳字幕に対応",
        "micro-LED デュアル — 576×288 / 4-bit greyscale (16 階調)。"
        "カメラ・スピーカーは非搭載、プライバシー重視の表示専用設計",
    ),
    (
        "約 36g・カメラなし、専用リング R1 でタップ操作",
        "HAO 設計 — 0.1mm FPC で左右ディスプレイを物理直結。"
        "G1 の無線同期を排除し、左右ズレ・遅延を構造的に解消",
    ),
]

# 5. BLE プロトコル 5 要点
SLIDE14 = [
    ("Google (Android XR)", "BLE プロトコル"),
    ("Gemini 搭載の 2 タイプ展開", "Even App と G2 の通信様式"),
    (
        "オーディオ型を先行発売。カメラ・マイク・スピーカーを内蔵し、Gemini Live と自然な会話ができます。",
        "接続: 左右テンプルが独立した BLE Peripheral。iPhone は 2 本の接続を張る "
        "(Even G2_XX_L_xxx / Even G2_XX_R_xxx)。BLE 5.4 + PAwR で衝突 50% 減。",
    ),
    (
        "ディスプレイ型を後続で投入。レンズにナビや翻訳字幕を表示し、視線を上げたまま道案内を受けられます。",
        "GATT: コマンド 0x5401 (Write) / 通知 0x5402 (Notify) / 描画 0x6402 (Write)。"
        "MTU 512、Interval 7.5–30ms。意味レイヤと描画レイヤを別チャネルに分離。",
    ),
    (
        "エージェント機能で、声色を再現した翻訳やコーヒー注文など複数手順の代行が可能です。",
        "パケット: 8 バイトヘッダ (AA 21 seq len 01 01 svc_hi svc_lo) + "
        "protobuf payload + CRC-16/CCITT (LE, 2 byte)。Payload のみが CRC 対象。",
    ),
    (
        "Android XR と iOS の両対応。Samsung・Qualcomm と共同開発し、49g のプロト試作機より軽量化を予定。",
        "サービス: 0x80xx 認証、0x06-20 Teleprompter、0x07-20 Dashboard、"
        "0x0B-20 Conversate など機能別に Service ID で分離。",
    ),
    (
        "発売は 2026 年秋後半から段階展開。ブランドは Warby Parker と Gentle Monster、日本展開と価格は未発表です。",
        "セッション: BLE 標準のボンディングは使わず、アプリ層で 7 パケットの"
        "ハンドシェイク（タイムスタンプ + トランザクション ID）でセッション確立。",
    ),
]

# 6. レイヤ別責務マップ (Comparison 4 cols)
SLIDE21 = [
    ("スペック比較", "レイヤ別の責務マップ"),
    ("Meta Ray-Ban", "プラグインコード"),
    ("Even G2", "Hub SDK + Bridge"),
    ("Google (Android XR)", "Even App + BLE"),
    ("観点", "観点"),
    # Meta 列 → プラグインコード
    ("カメラ 12MP / 3K 動画", "ページ定義とイベント処理"),
    ("重量 約 49〜51g、約 6.7 万円〜", "失敗症状: UI が出ない / 入力が来ない"),
    # Even 列 → SDK + Bridge
    ("ディスプレイ microLED 表示", "型付き API・イベント正規化・JS Bridge"),
    ("重量 約 36g、99,800 円", "失敗症状: waitForEvenAppBridge() が返らない"),
    # Google 列 → Even App + BLE
    ("Gemini 搭載、2 タイプ展開", "GATT 接続管理・パケット組立・CRC"),
    ("2026 年秋以降、日本展開は未発表", "失敗症状: 左右どちらかが切断 / Notify 不達"),
    # 観点列
    ("強み: 撮影 / 表示 / 統合", "扱う粒度"),
    ("日本販売: 済 / 済 / 未定", "障害の典型"),
]

# 7. まとめ
SLIDE25 = [
    ("まとめ", "まとめ"),
    (
        "Meta は外向きのデバイス。カメラとスピーカーで世界を撮る。普及台数は世界 700 万台超",
        "プラグイン JS はグラスでは走らない。iPhone の WebView 上で動き、"
        "BLE は Even App が中継する 3 層構成",
    ),
    (
        "Even は内向きのデバイス。カメラを省き、約 36g で常時着用向きの設計",
        "G2 の左右テンプルは別 BLE デバイス。ディスプレイは FPC で"
        "物理同期する HAO 設計で左右ズレを排除",
    ),
    (
        "Google は統合のデバイス。Gemini と 2 タイプ展開で両者の長所を取りに行く",
        "GATT は Write(0x5401) / Notify(0x5402) / Render(0x6402) の 3 本立て。"
        "MTU 512、CRC-16/CCITT",
    ),
    (
        "撮りたい人は Meta、目立たず見たい人は Even、待てる人は Google が向く",
        "Service ID で意味レイヤを分離。認証 0x80xx、Teleprompter 0x06-20、"
        "Dashboard 0x07-20 など機能別",
    ),
    (
        "判断軸は撮影・表示・デザイン・発売時期の 4 つ",
        "SDK は左右接続管理・CRC 計算・分割送信を全部隠す。"
        "プラグイン側は Web API 風の宣言だけで済む",
    ),
    (
        "鍵は Google の秋発売と日本展開",
        "コンテナ最大 4 / テキスト上限 / 4-bit 16 階調 などの制約は、"
        "下位ハードウェアの帯域とメモリから逆算されている",
    ),
]


REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "slide2.xml": SLIDE2,
    "slide8.xml": SLIDE8,
    "slide13.xml": SLIDE13,
    "slide15.xml": SLIDE15,
    "slide14.xml": SLIDE14,
    "slide21.xml": SLIDE21,
    "slide25.xml": SLIDE25,
    # slide39 (Thank you) はそのまま
}


def build() -> None:
    if not SRC_PPTX.exists():
        raise SystemExit(f"source pptx not found: {SRC_PPTX}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # 展開
        with zipfile.ZipFile(SRC_PPTX) as z:
            z.extractall(tmp_dir)

        # スライドごとに置換
        slides_dir = tmp_dir / "ppt" / "slides"
        for slide_name, pairs in REPLACEMENTS.items():
            slide_path = slides_dir / slide_name
            if not slide_path.exists():
                raise SystemExit(f"slide missing: {slide_path}")
            replace_each(slide_path, pairs)
            print(f"  replaced: {slide_name} ({len(pairs)} pairs)")

        # 再パッケージ（pptx は zip）
        if OUT_PPTX.exists():
            OUT_PPTX.unlink()
        with zipfile.ZipFile(OUT_PPTX, "w", zipfile.ZIP_DEFLATED) as z:
            for file in tmp_dir.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(tmp_dir).as_posix()
                    z.write(file, arcname)

        print(f"\nbuild OK: {OUT_PPTX}")
        print(f"  size: {OUT_PPTX.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
