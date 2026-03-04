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
yesterday = (now - timedelta(days=1)).strftime("%Y年%m月%d日")

TOPICS = [
    (
        "📱 モバイルアプリ開発",
        "昨日（{yesterday}）に配信・公開されたFlutter, iOS, App Store, インディー開発者に関するニュースやトレンドを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "🎨 UI/UX",
        "昨日（{yesterday}）に配信・公開されたモバイル・WebアプリのUI/UXデザイン、デザインシステム、ユーザー体験に関するニュースや事例を教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "📈 マーケティング",
        "昨日（{yesterday}）に配信・公開されたアプリマーケティング、ASO、個人開発者のグロース戦略に関するニュースを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "🤖 AI",
        "昨日（{yesterday}）に配信・公開された生成AI・LLM・個人開発者が使えるAIツールに関するニュースやリリース情報を教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "💰 マネタイズ",
        "昨日（{yesterday}）に配信・公開された個人開発アプリのマネタイズ事例、サブスク設計、フリーミアム戦略、価格設定に関するニュースを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
]


def get_previous_memo() -> str:
    """直近のメモファイルを取得する"""
    memo_dir = "memos"
    if not os.path.exists(memo_dir):
        return ""

    files = sorted([
        f for f in os.listdir(memo_dir) if f.endswith(".md")
    ])

    today_file = f"{date_str}.md"
    previous_files = [f for f in files if f != today_file]

    if not previous_files:
        return ""

    latest = previous_files[-1]
    with open(os.path.join(memo_dir, latest), "r", encoding="utf-8") as f:
        return f.read()


def search(query: str, previous_content: str = "") -> str:
    previous_instruction = ""
    if previous_content:
        previous_instruction = (
            f"\n\n以下は前回収集済みの情報です。この内容と重複するニュースや話題は除外し、"
            f"新しい情報・視点のみを提供してください。\n\n"
            f"---\n{previous_content[:3000]}\n---"
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
                    + previous_instruction
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
    previous_content = get_previous_memo()
    sections = []

    for category, query in TOPICS:
        print(f"Fetching: {category}")
        content = search(query.format(yesterday=yesterday), previous_content)
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
