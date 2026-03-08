import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta

PERPLEXITY_API_KEY = os.environ["PERPLEXITY_API_KEY"]
API_URL = "https://api.perplexity.ai/chat/completions"

JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
date_str = now.strftime("%Y-%m-%d")
timestamp = now.strftime("%Y-%m-%d %H:%M JST")

TOPICS = [
    (
        "📱 モバイルアプリ開発",
        "最新のFlutter, iOS, App Store, インディー開発者に関するニュースやトレンドを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "🎨 UI/UX",
        "最新のモバイル・WebアプリのUI/UXデザイン、デザインシステム、ユーザー体験に関するニュースや事例を教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "📈 マーケティング",
        "最新のアプリマーケティング、ASO、個人開発者のグロース戦略に関するニュースを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "🤖 AI",
        "最新の生成AI・LLM・個人開発者が使えるAIツールに関するニュースやリリース情報を教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "💰 マネタイズ",
        "最新の個人開発アプリのマネタイズ事例、サブスク設計、フリーミアム戦略、価格設定に関するニュースを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
]


def get_used_urls() -> str:
    """全期間のメモから収集済みURLを抽出する"""
    memo_dir = "memos"
    if not os.path.exists(memo_dir):
        return ""

    # 当月・前月のファイル名プレフィックスを生成
    urls = set()
    files = [
        f for f in os.listdir(memo_dir)
        if f.endswith(".md")
        and f != f"{date_str}.md"
    ]

    for filename in files:
        with open(os.path.join(memo_dir, filename), "r", encoding="utf-8") as f:
            content = f.read()
        # 参考リンクのURLを抽出（- [1] https://... の形式）
        for line in content.splitlines():
            if line.strip().startswith("- [") and "https://" in line:
                url = line.split("https://")[-1].strip()
                urls.add("https://" + url)

    return "\n".join(sorted(urls))


def search(query: str, used_urls: str = "") -> str:
    url_instruction = ""
    if used_urls:
        url_instruction = (
            "\n\n以下のURLはすでに過去に参照済みです。"
            "これらとまったく同じURLからの情報は使わないでください。"
            "同じドメインの別ページは使用して構いません。\n\n"
            + used_urls
        )

    payload = json.dumps({
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": (
                    "あなたは情報収集アシスタントです。"
                    "月収1万円を目指して個人でiOS/Chromeアプリを開発しているインディー開発者向けに、"
                    "実践的で示唆に富む情報を日本語でまとめてください。"
                    "・箇条書きで5点\n"
                    "・各項目は3〜4文で、具体的な数字や事例を必ず含めること\n"
                    "・「なぜ今重要か」を各項目に一言添えること\n"
                    "・最後に『💡 今週試せるアクション』を1つ、具体的に\n"
                    + url_instruction
                )
            },
            {"role": "user", "content": query}
        ],
        "max_tokens": 1000,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read())

    content = data["choices"][0]["message"]["content"]

    citations = data.get("citations", [])
    if citations:
        content += "\n\n**参考リンク**\n"
        for i, url in enumerate(citations, 1):
            content += f"- [{i}] {url}\n"

    return content


def main():
    used_urls = get_used_urls()  # ← 変更
    sections = []

    for category, query in TOPICS:
        print(f"Fetching: {category}")
        content = search(query, used_urls)
        sections.append(f"## {category}\n\n{content}\n")

    memo = f"""# 📚 アイデアストック — {date_str}

> 収集日時: {timestamp}

---

{"---\n\n".join(sections)}

---

## ✍️ 今日のアクション候補
<!-- 上記を読んで、今日試せることを1つ書く -->

"""

    os.makedirs("memos", exist_ok=True)
    filepath = f"memos/{date_str}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(memo)
    print(f"Saved: {filepath}")


if __name__ == "__main__":
    main()
