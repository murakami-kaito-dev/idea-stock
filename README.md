# 📚 idea-stock

毎日の情報収集を自動化し、アイデアのストックを積み上げるシステムです。
Perplexity APIのリアルタイム検索を使い、最新情報を日本語でまとめて `memos/` フォルダに保存します。

---

## システム構成図

```
【トリガー】
  手動実行（Actions タブ）
  または
  Issue 作成（GitHub モバイルから実行できるように作成）
        ↓
【GitHub Actions】
  Python スクリプトを 2段階で実行
        ↓
【Step 1: collect_ideas.py】
  カテゴリごとに Perplexity API へ問い合わせ
  → 引用番号 [N] を実URLに置換
  → memos/YYYY-MM-DD.md として保存
        ↓
【Step 2: filter_duplicates.py】
  過去メモの全URLと照合
  → 重複URLを含む項目を丸ごと除去
  → メモを上書き保存
        ↓
【memos/YYYY-MM-DD.md】
  GitHub リポジトリに自動コミット・プッシュ
  → GitHub モバイルでも閲覧可能
```

---

## スクリプトの処理ロジック

### Step 1: `scripts/collect_ideas.py`（情報収集）

#### 1. カテゴリごとに API 問い合わせ
`TOPICS` リストに定義された各カテゴリの質問文を Perplexity Sonar API に送信します。
レスポンスの本文と参考リンク（citations）を取得します。

#### 2. 引用番号をURLに置換
Perplexity API が返す `citations` 配列を使い、本文中の `[1]` `[2]` などの引用番号を実際のURLに置換します。
これにより、各項目の末尾にソースURLが直接埋め込まれます。

#### 3. Markdown に整形・保存
収集した情報をカテゴリ別に整形し、タイムスタンプ付きで `memos/YYYY-MM-DD.md` に保存します。

### Step 2: `scripts/filter_duplicates.py`（重複除去）

#### 1. 過去URLの収集
`memos/` フォルダ内の今日以外の全 Markdown ファイルからURLを抽出し、セットとして保持します。

#### 2. 項目ごとの重複チェック
今日のメモを空行区切りで項目に分割し、各項目に含まれるURLを過去URLセットと照合します。
一つでも重複があれば、その項目を丸ごと除去します。

#### 3. メモの上書き保存
フィルタ後に項目が残っていないカテゴリはセクションごとスキップし、メモを上書き保存します。

### 自動コミット
GitHub Actions の最終ステップで `git commit` & `git push` を実行し、生成されたメモをリポジトリに保存します。

---

## 重複排除の仕組み

このシステムでは **2段階パイプライン** を採用しています。

| 段階 | 担当 | 方式 |
|---|---|---|
| 収集 | `collect_ideas.py` | Perplexity API に問い合わせ、`[N]` → URL置換 |
| 除去 | `filter_duplicates.py` | 過去メモの全URLとプログラムで文字列一致 |

収集と除去を分離することで、AI のプロンプト指示に依存せず、プログラムの文字列一致で確実に重複を排除できます。

---

## 収集したい情報の編集方法

収集するトピックと質問文は `scripts/collect_ideas.py` の **`TOPICS`** リストで管理しています。

```python
TOPICS = [
    (
        "📱 モバイルアプリ開発",          # ← カテゴリ名（メモの見出しになる）
        "直近2ヶ月以内のFlutter, iOS, ..."  # ← 質問文
    ),
    ...
]
```

### カテゴリを追加する
タプル `(カテゴリ名, 質問文)` を `TOPICS` リストに追加するだけです。

```python
(
    "🔐 セキュリティ",
    "直近2ヶ月以内のモバイルアプリのセキュリティ脆弱性や対策に関するニュースを教えてください。英語・日本語どちらでも構いません。まとめは日本語で。"
),
```

### カテゴリを削除する
対応するタプルをまるごと削除してください。

### 質問文のポイント
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

### 3. カテゴリ数

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
│       └── idea-stock.yml       # GitHub Actions 設定
├── scripts/
│   ├── collect_ideas.py         # Step 1: 情報収集スクリプト
│   └── filter_duplicates.py     # Step 2: 重複除去スクリプト
├── memos/
│   ├── 2026-03-04.md            # 自動生成されるメモ
│   └── 2026-03-05.md
└── README.md
```
