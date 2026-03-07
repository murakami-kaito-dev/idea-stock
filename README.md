# 📚 idea-stock

毎日の情報収集を自動化し、アイデアのストックを積み上げるシステムです。
Perplexity APIのリアルタイム検索を使い、前日に配信された最新情報を日本語でまとめて `memos/` フォルダに保存します。

---

## システム構成図

```
【トリガー】
  手動実行（Actions タブ）
  または
  Issue 作成（GitHub モバイルから実行できるように作成）
        ↓
【GitHub Actions】
  Python スクリプトを実行
        ↓
【collect_ideas.py】
  1. 前回メモを読み込む（memos/ フォルダの直近ファイル）
  2. 昨日の日付を生成
  3. カテゴリごとに Perplexity API へ問い合わせ
  4. 結果を Markdown に整形
  5. memos/YYYY-MM-DD.md として保存
        ↓
【Perplexity Sonar API】
  リアルタイム Web 検索（英語・日本語）
  → 前日配信の情報を要約して返答
        ↓
【memos/YYYY-MM-DD.md】
  GitHub リポジトリに自動コミット・プッシュ
  → GitHub モバイルでも閲覧可能
```

---

## スクリプトの処理ロジック

`scripts/collect_ideas.py` は以下の順で動作します。

### 1. 前回メモの読み込み
`memos/` フォルダ内の Markdown ファイルを日付順にソートし、今日以外の直近1件を読み込みます。
これを Perplexity API に渡すことで、前回と重複する情報を除外します。

### 2. 昨日の日付を生成
JST（日本標準時）で「昨日」の日付文字列を生成し、質問文に埋め込みます。
これにより「昨日配信された情報」に絞った検索が可能になります。

### 3. カテゴリごとに API 問い合わせ
`TOPICS` リストに定義された各カテゴリの質問文を Perplexity Sonar API に送信します。
レスポンスの本文と参考リンク（citations）を取得します。

### 4. Markdown に整形・保存
収集した情報をカテゴリ別に整形し、タイムスタンプ付きで `memos/YYYY-MM-DD.md` に保存します。

### 5. 自動コミット
GitHub Actions の最終ステップで `git commit` & `git push` を実行し、生成されたメモをリポジトリに保存します。

---

## 収集したい情報の編集方法

収集するトピックと質問文は `scripts/collect_ideas.py` の **`TOPICS`** リストで管理しています。

```python
TOPICS = [
    (
        "📱 モバイルアプリ開発",          # ← カテゴリ名（メモの見出しになる）
        "昨日（{yesterday}）に配信・公開されたFlutter, iOS, ..."  # ← 質問文
    ),
    ...
]
```

### カテゴリを追加する
タプル `(カテゴリ名, 質問文)` を `TOPICS` リストに追加するだけです。

```python
(
    "🔐 セキュリティ",
    "昨日（{yesterday}）に配信・公開されたモバイルアプリのセキュリティ脆弱性や対策に関するニュースを教えてください。英語・日本語どちらでも構いません。まとめは日本語で。"
),
```

### カテゴリを削除する
対応するタプルをまるごと削除してください。

### 質問文のポイント
- `{yesterday}` はスクリプトが自動で前日の日付に置換します。必ず含めてください。
- 「英語・日本語どちらでも構いません。まとめは日本語で。」を末尾に入れると情報量が増えます。

---

## アイデアメモを収集する方法

### 方法①：Actions タブから手動実行（PC 向け）

1. GitHub リポジトリの **「Actions」** タブを開く
2. 左サイドバーの **「Daily Idea Stock」** をクリック
3. **「Run workflow」** → **「Run workflow」** をクリック
4. 1〜2分後に `memos/YYYY-MM-DD.md` が生成される

### 方法②：Issue を作成して実行（モバイル向け）

GitHub モバイルアプリには Actions タブがないため、Issue 作成をトリガーにしています。

1. GitHub モバイルアプリでリポジトリを開く
2. **「Issues」** → **「+」** で新規 Issue を作成
3. タイトル・本文は何でも構わない（例：「run」）
4. Issue を作成するだけで Actions が自動起動する
5. 実行後は Issue を Close しておくと履歴がすっきりする

---

## ※ 自動実行のスケジュール設定

毎日決まった時刻に自動実行したい場合は `.github/workflows/idea-stock.yml` の `on:` セクションに `schedule` を追加します。

```yaml
on:
  workflow_dispatch:   # 手動実行
  issues:
    types: [opened]    # Issue 作成でトリガー
  schedule:
    - cron: '0 1 * * *'  # ← 毎日 JST 10:00 に自動実行（UTC 01:00）
```

### cron 記法の説明

```
'0 1 * * *'
 ┬ ┬ ┬ ┬ ┬
 │ │ │ │ └── 曜日（* = 毎日）
 │ │ │ └──── 月（* = 毎月）
 │ │ └────── 日（* = 毎日）
 │ └──────── 時（UTC。JST = UTC+9 なので、JST 10:00 = UTC 01:00）
 └────────── 分
```

### よく使う時刻の例

| 実行したい時刻（JST） | cron 設定 |
|---|---|
| 毎朝 7:00 | `'0 22 * * *'`（前日 UTC 22:00） |
| 毎朝 8:00 | `'0 23 * * *'`（前日 UTC 23:00） |
| 毎朝 10:00 | `'0 1 * * *'` |
| 平日のみ 9:00 | `'0 0 * * 1-5'` |

---

## 情報収集量の調整

収集する情報の量は `scripts/collect_ideas.py` の以下の箇所で調整できます。

### 1. 各カテゴリの出力量（`max_tokens`）

```python
payload = json.dumps({
    "model": "sonar",
    ...
    "max_tokens": 1000,  # ← ここを変える
})
```

| 設定値 | 目安 |
|---|---|
| `500` | 短め・要点のみ |
| `1000` | 標準（現在の設定） |
| `2000` | 詳細・読み応えあり |

### 2. システムプロンプトの箇条書き数

```python
"・箇条書きで5点\n"          # ← 点数を変える（例：3点〜10点）
"・各項目は3〜4文で\n"        # ← 1項目あたりの文数を変える
```

### 3. 前回メモの参照量

```python
f"---\n{previous_content[:3000]}\n---"  # ← 3000文字を変える
```

文字数を増やすほど重複除外の精度が上がりますが、トークン消費も増えます。

### 4. カテゴリ数

`TOPICS` リストのカテゴリ数が多いほど実行時間とコストが増加します。
現在5カテゴリで1回あたり約3〜4円（Perplexity Sonar API）が目安です。

---

## APIキーの設定

Perplexity API キーは GitHub Secrets に登録します。

1. リポジトリの **「Settings」→「Secrets and variables」→「Actions」**
2. **「New repository secret」** をクリック
3. `Name: PERPLEXITY_API_KEY`、`Secret: your_api_key` を入力

---
## Perplexity API キーの作成手順

### 1. アカウント作成

1. [https://www.perplexity.ai](https://www.perplexity.ai) にアクセス
2. **「Sign Up」** をクリック
3. Google アカウントまたはメールアドレスで登録

### 2. API ページへ移動

1. ログイン後、右上のアイコンをクリック
2. **「Settings」** を開く
3. 左サイドバーの **「API」** をクリック

### 3. 支払い方法の登録

API はプリペイド制のため、事前にクレジットを購入する必要があります。

1. **「Add Payment Method」** をクリックしてクレジットカードを登録
2. **「Buy Credits」** をクリックしてクレジットを購入（最小 $5 から）
3. **「Automatic Top-Up」は OFF のまま**にしておくと上限管理できて安心

### 4. API キーの作成

1. **「API Keys」** セクションの **「+ Create Key」** をクリック
2. キーの名前を入力（例：`idea-stock`）
3. **「Create」** をクリック
4. 表示された API キーをすぐコピーして安全な場所に保存
   ⚠️ キーはこの画面を離れると二度と表示されません

### 5. GitHub Secrets への登録

上記「APIキーの設定」セクションの手順に従って、コピーしたキーを登録してください。

---

## フォルダ構成

```
idea-stock/
├── .github/
│   └── workflows/
│       └── idea-stock.yml   # GitHub Actions 設定
├── scripts/
│   └── collect_ideas.py     # 情報収集スクリプト（編集はここ）
├── memos/
│   ├── 2026-03-04.md        # 自動生成されるメモ
│   └── 2026-03-05.md
└── README.md
```
