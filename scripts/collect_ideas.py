import os
import re
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
        "直近2ヶ月以内のFlutter, iOS, App Store, インディー開発者に関するニュースやトレンドを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "🎨 UI/UX",
        "直近2ヶ月以内のモバイル・WebアプリのUI/UXデザイン、デザインシステム、ユーザー体験に関するニュースや事例を教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "📈 マーケティング",
        "直近2ヶ月以内のアプリマーケティング、ASO、個人開発者のグロース戦略に関するニュースを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "🤖 AI",
        "直近2ヶ月以内の生成AI・LLM・個人開発者が使えるAIツールに関するニュースやリリース情報を教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
    (
        "💰 マネタイズ",
        "直近2ヶ月以内の個人開発アプリのマネタイズ事例、サブスク設計、フリーミアム戦略、価格設定に関するニュースを教えてください。英語・日本語どちらの情報源でも構いません。まとめは日本語で。"
    ),
]


def search(query: str) -> str | None:
    messages = [
        {
            "role": "system",
            "content": (
                "あなたは情報収集アシスタントです。"
                "月収1万円を目指して個人でiOS/Chromeアプリを開発しているインディー開発者向けに、"
                "実践的で示唆に富む情報を日本語でまとめてください。\n"
                "・箇条書きで5点\n"
                "・各項目は3〜4文で、具体的な数字や事例を必ず含めること\n"
                "・「なぜ今重要か」を各項目に一言添えること\n"
                "・各項目の末尾に、その項目の主要な情報源の引用番号[N]を必ず1つだけ付けること\n"
                "・1つの項目に複数の[N]を混在させないこと。最も重要な情報源1つに絞ること\n"
            )
        },
        {"role": "user", "content": query},
    ]

    payload = json.dumps({
        "model": "sonar",
        "messages": messages,
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

    if not citations:
        return None

    # 本文中の[N]を実際のURLに直接置換
    def replace_citation(match):
        num = int(match.group(1))
        if num <= len(citations):
            return citations[num - 1]
        return ""

    content = re.sub(r'\[(\d+)\]', replace_citation, content)

    # URLだけの行を除去（[N]置換後にURLが二重になるのを防止）
    url_only_pattern = re.compile(r'^\s*https?://[^\s]+\s*$')
    lines = content.split('\n')
    cleaned_lines = [line for line in lines if not url_only_pattern.match(line)]
    content = '\n'.join(cleaned_lines)

    return content


def main():
    sections = []
    collected = []
    skipped = []

    for category, query in TOPICS:
        print(f"Fetching: {category}")
        content = search(query)
        if content is None:
            print(f"  → 情報源なし、スキップ: {category}")
            skipped.append(category)
            continue
        sections.append(f"## {category}\n\n{content}\n")
        collected.append(category)

    # サマリーログ
    print(f"\n===== 収集結果サマリー =====")
    print(f"収集成功: {len(collected)}カテゴリ ({', '.join(collected)})")
    if skipped:
        print(f"スキップ: {len(skipped)}カテゴリ ({', '.join(skipped)})")

    memo = f"""# 📚 アイデアストック — {date_str}

> 収集日時: {timestamp}

---

{"---\n\n".join(sections)}

---

"""

    os.makedirs("memos", exist_ok=True)
    filepath = f"memos/{date_str}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(memo)
    print(f"Saved: {filepath}")


if __name__ == "__main__":
    main()
