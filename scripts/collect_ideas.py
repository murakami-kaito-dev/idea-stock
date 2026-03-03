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
        "今週のFlutter, iOS, App Store審査, インディー開発者向けの最新ニュースやトレンドを教えてください。日本語で。"
    ),
    (
        "🎨 UI/UX",
        "今週のモバイルUI/UXデザイン、デザインシステム、ユーザー体験に関する最新トレンドや事例を教えてください。日本語で。"
    ),
    (
        "📈 マーケティング",
        "今週のアプリマーケティング、ASO（アプリストア最適化）、個人開発者のグロース戦略に関する最新情報を教えてください。日本語で。"
    ),
    (
        "🤖 AI",
        "今週の生成AI・LLM・個人開発者が使えるAIツールに関する最新ニュースやリリース情報を教えてください。日本語で。"
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
                    "個人でアプリを開発しているインディー開発者向けに、"
                    "実践的で示唆に富む情報を日本語で簡潔にまとめてください。"
                    "・箇条書きで3〜5点\n"
                    "・各項目は2〜3文で具体的に\n"
                    "・最後に『💡 So What?（自分への問い）』を1つ"
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
