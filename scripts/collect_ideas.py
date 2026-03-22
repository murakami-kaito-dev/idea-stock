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
 
 
def get_used_urls() -> set:
    """全期間のメモから収集済みURLをセットで返す"""
    memo_dir = "memos"
    if not os.path.exists(memo_dir):
        return set()
 
    urls = set()
    files = [
        f for f in os.listdir(memo_dir)
        if f.endswith(".md")
        and f != f"{date_str}.md"
    ]
 
    url_pattern = re.compile(r'https?://[^\s\)]+')
 
    for filename in files:
        with open(os.path.join(memo_dir, filename), "r", encoding="utf-8") as f:
            content = f.read()
        for match in url_pattern.findall(content):
            urls.add(match)
 
    return urls
 
 
def search(query: str, already_used: set) -> str | None:
    url_instruction = ""
    if already_used:
        url_instruction = (
            "【厳守事項】以下のURLはすでに過去に取得済みです。"
            "これらのURLを情報源として使用することを固く禁じます。"
            "必ず異なるURLの情報源から回答してください。"
            "同じドメインの別ページは使用して構いません。\n\n"
            + "\n".join(sorted(already_used))
        )
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
    ]
 
    if url_instruction:
        messages.append({"role": "user", "content": url_instruction})
        messages.append({"role": "assistant", "content": "承知しました。指定のURLは使用しません。"})
    messages.append({"role": "user", "content": query})
 
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
 
    # citationsがない場合はNoneを返してスキップ
    if not citations:
        return None
 
    # citations辞書を構築（1-indexed）
    citation_map = {}
    for i, url in enumerate(citations, 1):
        if url not in already_used:
            citation_map[i] = url
 
    # 除外後にcitationsが全滅した場合もスキップ
    if not citation_map:
        return None
 
    # 本文中の[N]を実際のURLに置換
    # 除外対象のURLの[N]は削除、有効なURLの[N]は実URLに置換
    def replace_citation(match):
        num = int(match.group(1))
        if num in citation_map:
            return citation_map[num]
        # citation_mapにない場合、元のcitationsから直接引く
        if num <= len(citations):
            return citations[num - 1]
        return ""

    content = re.sub(r'\[(\d+)\]', replace_citation, content)
 
    return content
 
 
def main():
    already_used = get_used_urls()
    sections = []
 
    for category, query in TOPICS:
        print(f"Fetching: {category}")
        content = search(query, already_used)
        if content is None:
            print(f"  情報源なし、スキップ: {category}")
            continue
        sections.append(f"## {category}\n\n{content}\n")
 
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
 
