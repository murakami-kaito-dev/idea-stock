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
        "今日から1週間以内のFlutter, iOS, App Store審査, インディー開発者向けの最新ニュースやトレンドを調査して、日本語で教えてください。"
    ),
    (
        "🎨 UI/UX",
        "今日から1週間以内のモバイルアプリのUI/UXデザイン、WebアプリのUI/UXデザイン、デザインシステム、ユーザー体験に関する最新トレンドや事例を調査して、日本語で教えてください。"
    ),
    (
        "📈 マーケティング",
        "今日から1週間以内のアプリマーケティング、ASO（アプリストア最適化）、個人開発者のグロース戦略に関する最新情報を調査して、日本語で教えてください。"
    ),
    (
        "🤖 AI",
        "今日から1週間以内の生成AI・LLM・個人開発者が使えるAIツールに関する最新ニュースやリリース情報を調査して、日本語で教えてください。"
    ),
    (
        "💰 マネタイズ",
        "今日から1か月以内の個人開発アプリのマネタイズ事例、サブスク設計、"
        "フリーミアム戦略、価格設定、マーケティング戦略に関する最新情報を調査して、日本語で教えてください。"
    ),
]


def search(query: str) -> str:
    payload = json.dumps({
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": (
                    "あなたは情報収集アシスタントです。"
                    "月収1万円を目指して個人でモバイル（iOS・Android）/Chromeアプリを開発しているインディー開発者向けに、"
                    "実践的で示唆に富む情報を日本語でまとめてください。"
                    "・箇条書きで5点\n"
                    "・各項目は4～5文で、具体的な数字や事例を必ず含めること\n"
                    "・「なぜ今重要か」を各項目に一言添えること\n"
                    "・最後に『💡 今週試せるアクション』を1つ、具体的に\n"
                )
            },
            {"role": "user", "content": query}
        ],
        "max_tokens": 1150,
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
    
    # citationsを取り出してURLリストを追記
    citations = data.get("citations", [])
    if citations:
        content += "\n\n**参考リンク**\n"
        for i, url in enumerate(citations, 1):
            content += f"- [{i}] {url}\n"
    
    return content


def main():
    sections = []

    for category, query in TOPICS:
        print(f"Fetching: {category}")
        content = search(query)
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
