#!/usr/bin/env python3

import hashlib, json, os, re, time, urllib.parse 
from pathlib import Path
from typing import Any
from urllib import request, error
from dotenv import load_dotenv
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
POSTS_DB_ID = os.getenv("NOTION_POSTS_DB_ID")

BASE_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = BASE_DIR / "_posts"
INDEX_PATH = BASE_DIR / "scripts/.notion_index.json"

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

def notion_request(method: str, path: str, payload: dict[str, Any] | None = None):
    url = f"{NOTION_API_BASE}{path}"
    body = json.dumps(payload).encode("utf-8") if payload else None

    req = request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )

    for _ in range(5):
        try:
            with request.urlopen(req, timeout=60) as res:
                raw = res.read().decode()
                time.sleep(0.2)
                return json.loads(raw) if raw else {}
        except error.HTTPError as e:
            if e.code == 429:
                time.sleep(1)
                continue
            if e.code == 403:
                time.sleep(3)
                continue
            raise RuntimeError(e.read().decode())

def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {}

def save_index(index):
    tmp = INDEX_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, separators=(",", ":")))
    tmp.replace(INDEX_PATH)

def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def parse_frontmatter(raw):
    m = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", raw, re.DOTALL)
    if not m:
        return {}, raw

    fm = {}
    current = None

    for line in m.group(1).splitlines():
        if line.startswith("- ") and current:
            fm.setdefault(current, []).append(line[2:].strip())
        elif ":" in line:
            k, v = line.split(":", 1)
            current = k.strip()
            v = v.strip()
            if not v:
                fm[current] = []
            else:
                fm[current] = v.strip("'\"")

    return fm, m.group(2)

def html_to_blocks(content):
    blocks = []

    patterns = re.findall(
        r"<h[1-3][^>]*>.*?</h[1-3]>|<p[^>]*>.*?</p>|<li[^>]*>.*?</li>|<img[^>]*>",
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    for chunk in patterns:
        tag = re.match(r"<\s*([a-zA-Z0-9]+)", chunk)
        text = re.sub(r"<[^>]+>", "", chunk)
        text = re.sub(r"\s+", " ", text).strip()

        if not tag:
            continue

        t = tag.group(1).lower()

        if t == "img":
            src_match = re.search(r'src="([^"]+)"', chunk)
            if src_match:
                src = src_match.group(1)

                if src.startswith("/image/"):
                    encoded = src.split("/image/")[1].split("?")[0]
                    src = urllib.parse.unquote(encoded)

                filename = src.split("/")[-1]
                src = f"https://github.insightginie.com/media/images/{filename}"

                blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {"type": "external", "external": {"url": src}}
                })
            continue

        block_type = {
            "h1": "heading_1",
            "h2": "heading_2",
            "h3": "heading_3",
            "li": "bulleted_list_item"
        }.get(t, "paragraph")

        blocks.append({
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": [{"type": "text", "text": {"content": text[:1900]}}]
            }
        })

    return blocks

def get_children(block_id):
    results = []
    cursor = None

    while True:
        path = f"/blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"

        res = notion_request("GET", path)
        results.extend(res.get("results", []))

        if not res.get("has_more"):
            break

        cursor = res.get("next_cursor")

    return results

def delete_all_blocks(page_id):
    for b in get_children(page_id):
        notion_request("DELETE", f"/blocks/{b['id']}")

def append_blocks(page_id, blocks):
    for i in range(0, len(blocks), 100):
        notion_request("PATCH", f"/blocks/{page_id}/children", {
            "children": blocks[i:i+100]
        })
        time.sleep(0.3)

def extract_categories(path: Path):
    rel = path.relative_to(POSTS_DIR)
    parts = rel.parts[:-1]
    cat = parts[0] if len(parts) > 0 else ""
    sub = parts[1] if len(parts) > 1 else ""
    return cat.lower(), sub.lower()

def get_changes(index):
    out = []
    for p in POSTS_DIR.rglob("*.md"):
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
        h = file_hash(p)

        if slug not in index:
            out.append((p, "new", h))
        elif index[slug]["h"] != h:
            out.append((p, "update", h))

    return out

def sync_post(path: Path, index, mode, h):
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)

    title = fm.get("title")
    if isinstance(title, list):
        title = " ".join(title)
    if not title:
        title = slug

    date = fm.get("date")
    url = fm.get("original_url", "")
    cat, sub = extract_categories(path)

    img = fm.get("featured_image")
    if img:
        filename = img.split("/")[-1]
        img = f"https://github.insightginie.com/media/images/{filename}"

    props = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Slug": {"rich_text": [{"text": {"content": slug}}]},
        "Category": {"rich_text": [{"text": {"content": cat}}]},
        "Sub-category": {"rich_text": [{"text": {"content": sub}}]},
    }

    if date:
        props["Date"] = {"date": {"start": date}}

    if url:
        props["Source URL"] = {"url": url}

    blocks = html_to_blocks(body)

    if mode == "new":
        payload = {
            "parent": {"database_id": POSTS_DB_ID},
            "properties": props
        }

        if img:
            payload["cover"] = {"type": "external", "external": {"url": img}}

        res = notion_request("POST", "/pages", payload)
        notion_id = res["id"]

        append_blocks(notion_id, blocks)

    else:
        notion_id = index[slug]["n"]
        notion_request("PATCH", f"/pages/{notion_id}", {"properties": props})
        delete_all_blocks(notion_id)
        append_blocks(notion_id, blocks)

    index[slug] = {"h": h, "n": notion_id}

def main():
    index = load_index()
    changes = get_changes(index)

    print("to process:", len(changes))

    for p, m, h in changes:
        try:
            sync_post(p, index, m, h)
        except Exception as e:
            print("error:", e)

        save_index(index)

    print("done")

if __name__ == "__main__":
    main()