import os
import sys
import requests
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from sitemap import regenerate_full_sitemap

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "scripts/last_sync.json"

SITE = "https://insightginie.com"
POST_API = f"{SITE}/wp-json/wp/v2/posts"

PER_PAGE = 100
MAX_WORKERS = 10
POSTS_PER_PAGE = 100

def load_state():
    if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"last_id": 0, "posts": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def sanitize(content):
    content = re.sub(r"<script.*?>.*?</script>", "", content, flags=re.DOTALL)
    content = content.replace("{%", "{% raw %}{%")
    content = content.replace("%}", "%}{% endraw %}")
    return content

def generate_sitemap(all_posts):
    url_list = []
    for post in all_posts:
        url_list.append({"url": f"https://aloycwl.github.io/{post['slug']}", "lastmod": post["date"][:10]})
    total_pages = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for page_num in range(1, total_pages + 1):
        url_list.append({"url": f"https://aloycwl.github.io/page/{page_num}/", "lastmod": all_posts[0]["date"][:10]})
    regenerate_full_sitemap(url_list)

def render_index(all_posts):
    total = len(all_posts)
    pages = (total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    data_dir = BASE_DIR / "data"
    page_dir_base = BASE_DIR / "page"
    data_dir.mkdir(exist_ok=True)
    page_dir_base.mkdir(exist_ok=True)

    with open(data_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"latest_page": pages, "posts_per_page": POSTS_PER_PAGE, "total_posts": total}, f)

    for page_num in range(1, pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        page_posts = all_posts[start:start + POSTS_PER_PAGE]
        listing_posts = {
            post["slug"]: {"title": post["title"], "date": post["date"][:10], "excerpt": post["excerpt"]}
            for post in page_posts
        }

        page_dir = page_dir_base / str(page_num)
        page_dir.mkdir(exist_ok=True)
        with open(page_dir / f"{page_num}.json", "w", encoding="utf-8") as f:
            json.dump(listing_posts, f)

        page_html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>InsightGinie - Page {page_num}</title><script>window.location = "/?page={page_num}";</script></head><body>Redirecting...</body></html>'''
        with open(page_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(page_html)

def reset_sync_state():
    for folder in [BASE_DIR / "data", BASE_DIR / "page"]:
        folder.mkdir(exist_ok=True)
        for child in folder.iterdir():
            if child.is_dir():
                import shutil
                shutil.rmtree(child)
            else:
                child.unlink()
    if STATE_FILE.exists():
        STATE_FILE.unlink()

def sync(max_posts=None, full_resync=False):
    if full_resync:
        print("Running full resync: clearing local sync state...")
        reset_sync_state()

    state = load_state()
    last_id = state.get("last_id", 0)
    processed_posts = state.get("posts", {})
    ThreadPoolExecutor(max_workers=MAX_WORKERS)
    page = 1
    processed = 0
    stop = False
    max_id = last_id

    print(f"Starting sync. Last synced post ID: {last_id}")
    while True:
        url = f"{POST_API}?per_page={PER_PAGE}&page={page}&_embed&orderby=id&order=desc&status=publish"
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            break
        posts = r.json()
        if not posts:
            break

        for post in posts:
            if max_posts is not None and processed >= max_posts:
                stop = True
                break
            if post["id"] <= last_id:
                stop = True
                break

            title = post["title"]["rendered"]
            slug = post["slug"]
            date = post["date_gmt"] + "+00:00"
            content = sanitize(post["content"]["rendered"])
            excerpt = re.sub(r'<[^>]+>', '', post.get("excerpt", {}).get("rendered", "")).strip()[:160]
            image = f"https://picsum.photos/seed/{slug}/800/400"

            processed_posts[str(post["id"])] = {"id": post["id"], "slug": slug, "title": title, "date": date, "excerpt": excerpt}
            with open(BASE_DIR / "data" / f"{slug}.json", "w", encoding="utf-8") as f:
                json.dump({"content": content, "img": image, "date": date[:10], "excerpt": excerpt, "title": title, "slug": slug}, f)

            max_id = max(max_id, post["id"])
            processed += 1
        if stop:
            break
        page += 1

    all_posts = sorted(processed_posts.values(), key=lambda x: x["date"], reverse=True)
    render_index(all_posts)
    generate_sitemap(all_posts)
    state["last_id"] = max_id
    state["posts"] = processed_posts
    save_state(state)
    print(f"Done. Processed {processed} new posts. Total posts: {len(processed_posts)}")

if __name__ == "__main__":
    args = sys.argv[1:]
    max_posts = None
    full_resync = False
    for arg in args:
        if arg.isdigit():
            max_posts = int(arg)
        elif arg in {"--full", "--reset", "full"}:
            full_resync = True
    sync(max_posts=max_posts, full_resync=full_resync)
