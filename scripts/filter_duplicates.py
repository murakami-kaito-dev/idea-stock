"""
filter_duplicates.py
--------------------
今日生成されたメモから、過去のメモに含まれるURLと重複する項目を除去する。
collect_ideas.py の後に実行する。
"""

import os
import re
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
date_str = datetime.now(JST).strftime("%Y-%m-%d")

MEMO_DIR = "memos"
TODAY_FILE = os.path.join(MEMO_DIR, f"{date_str}.md")

URL_PATTERN = re.compile(r'https?://[^\s\)\]。、，．）】」』\u3000]+')


def get_past_urls() -> set:
    """今日以外の全メモからURLを収集"""
    urls = set()
    if not os.path.exists(MEMO_DIR):
        return urls

    for filename in os.listdir(MEMO_DIR):
        if not filename.endswith(".md"):
            continue
        if filename == f"{date_str}.md":
            continue
        with open(os.path.join(MEMO_DIR, filename), "r", encoding="utf-8") as f:
            for match in URL_PATTERN.findall(f.read()):
                urls.add(match)

    return urls


def split_into_sections(memo: str) -> tuple[str, list[tuple[str, str]], str]:
    """
    メモをヘッダー部分・カテゴリセクション・フッターに分割。
    Returns: (header, [(category_heading, body), ...], footer)
    """
    # ## で始まるカテゴリ見出しで分割
    section_pattern = re.compile(r'^(## .+)$', re.MULTILINE)
    splits = section_pattern.split(memo)

    # splits[0] はヘッダー（## より前の部分）
    header = splits[0]
    sections = []

    for i in range(1, len(splits), 2):
        heading = splits[i]
        body = splits[i + 1] if i + 1 < len(splits) else ""
        sections.append((heading, body))

    # フッターの処理: 最後のセクション本文末尾の "---" 以降
    footer = ""
    if sections:
        last_heading, last_body = sections[-1]
        # 最終セクションの末尾にある最後の "---" をフッターとして分離
        footer_match = re.search(r'\n---\s*\n*$', last_body)
        if footer_match:
            footer = last_body[footer_match.start():]
            sections[-1] = (last_heading, last_body[:footer_match.start()])

    return header, sections, footer


def filter_items(body: str, past_urls: set) -> str:
    """
    セクション本文内の各項目を解析し、過去URLを含む項目を除去。
    項目は空行で区切られたブロックとして扱う。
    """
    # 空行で項目を分割（Perplexityの出力は項目間に空行が入る）
    blocks = re.split(r'\n{2,}', body.strip())

    kept = []
    removed_count = 0

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # ブロック内のURLを抽出
        urls_in_block = set(URL_PATTERN.findall(block))

        # 過去URLと一つでも重複があれば除去
        if urls_in_block & past_urls:
            removed_count += 1
            continue

        kept.append(block)

    if removed_count > 0:
        print(f"  → {removed_count}件の重複項目を除去")

    return "\n\n".join(kept)


def main():
    if not os.path.exists(TODAY_FILE):
        print(f"今日のメモが見つかりません: {TODAY_FILE}")
        return

    with open(TODAY_FILE, "r", encoding="utf-8") as f:
        memo = f.read()

    past_urls = get_past_urls()
    if not past_urls:
        print("過去メモなし。フィルタ不要。")
        return

    print(f"過去メモから {len(past_urls)} 件のURLを検出")

    header, sections, footer = split_into_sections(memo)

    filtered_sections = []
    for heading, body in sections:
        print(f"処理中: {heading.strip()}")
        filtered_body = filter_items(body, past_urls)

        # フィルタ後に項目が残っていればセクションを保持
        if filtered_body.strip():
            filtered_sections.append(f"{heading}\n\n{filtered_body}\n")
        else:
            print(f"  → 全項目が重複のためカテゴリごとスキップ")

    # メモを再構築
    result = header
    result += "---\n\n".join(filtered_sections)
    result += footer

    with open(TODAY_FILE, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"フィルタ完了: {TODAY_FILE}")


if __name__ == "__main__":
    main()
