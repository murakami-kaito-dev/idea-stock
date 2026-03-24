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
RAW_FILE = os.path.join(MEMO_DIR, f"{date_str}-raw.md")
FILTERED_FILE = os.path.join(MEMO_DIR, f"{date_str}.md")

URL_PATTERN = re.compile(r'https?://[^\s\)\]。、，．）】」』\u3000]+')


def get_past_urls() -> set:
    """今日以外の全メモからURLを収集"""
    urls = set()
    if not os.path.exists(MEMO_DIR):
        return urls

    for filename in os.listdir(MEMO_DIR):
        if not filename.endswith(".md"):
            continue
        if filename == f"{date_str}.md" or filename == f"{date_str}-raw.md":
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


def split_into_items(body: str) -> list[str]:
    """
    セクション本文を個別の項目に分割する。
    箇条書きマーカー（-、•、*、数字.）で始まる行を項目の開始とみなす。
    マーカーが見つからない場合は空行で分割する。
    """
    lines = body.strip().split('\n')
    # 箇条書きマーカーのパターン
    bullet_pattern = re.compile(r'^\s*[-•*]\s|^\s*\d+[.)]\s')

    # まず箇条書きマーカーがあるか確認
    has_bullets = any(bullet_pattern.match(line) for line in lines if line.strip())

    if has_bullets:
        # マーカーで分割
        items = []
        current = []
        for line in lines:
            if bullet_pattern.match(line) and current:
                items.append('\n'.join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            items.append('\n'.join(current))
        return [item.strip() for item in items if item.strip()]
    else:
        # マーカーがなければ空行で分割
        blocks = re.split(r'\n{2,}', body.strip())
        return [b.strip() for b in blocks if b.strip()]


def filter_items(body: str, past_urls: set) -> str:
    """
    セクション本文内の各項目を解析し、過去URLを含む項目を除去。
    """
    blocks = split_into_items(body)

    kept = []
    removed_count = 0

    for block in blocks:
        if not block:
            continue

        # ブロック内のURLを抽出
        urls_in_block = set(URL_PATTERN.findall(block))

        # 過去URLと一つでも重複があれば除去
        if urls_in_block & past_urls:
            dup_urls = urls_in_block & past_urls
            removed_count += 1
            print(f"    除去: {list(dup_urls)[0]}")
            continue

        kept.append(block)

    if removed_count > 0:
        print(f"  → {removed_count}件の重複項目を除去")

    return "\n\n".join(kept)


def main():
    if not os.path.exists(RAW_FILE):
        print(f"今日のrawメモが見つかりません: {RAW_FILE}")
        return

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        memo = f.read()

    past_urls = get_past_urls()
    if not past_urls:
        print("過去メモなし。rawをそのままコピー。")
        with open(FILTERED_FILE, "w", encoding="utf-8") as f:
            f.write(memo)
        print(f"Saved: {FILTERED_FILE}")
        return

    print(f"過去メモから {len(past_urls)} 件のURLを検出")

    header, sections, footer = split_into_sections(memo)

    filtered_sections = []
    skipped_categories = []

    for heading, body in sections:
        print(f"処理中: {heading.strip()}")
        filtered_body = filter_items(body, past_urls)

        # フィルタ後に項目が残っていればセクションを保持
        if filtered_body.strip():
            filtered_sections.append(f"{heading}\n\n{filtered_body}\n")
        else:
            skipped_categories.append(heading.strip())
            print(f"  → 全項目が重複のためカテゴリごとスキップ")

    # メモを再構築
    result = header
    result += "---\n\n".join(filtered_sections)
    result += footer

    with open(FILTERED_FILE, "w", encoding="utf-8") as f:
        f.write(result)

    # サマリーログ
    print(f"\n===== フィルタ結果サマリー =====")
    print(f"入力カテゴリ数: {len(sections)}")
    print(f"出力カテゴリ数: {len(filtered_sections)}")
    if skipped_categories:
        print(f"全除去されたカテゴリ: {', '.join(skipped_categories)}")
    print(f"フィルタ完了: {FILTERED_FILE}")


if __name__ == "__main__":
    main()
