import sys
import requests
import json
import re
from pathlib import Path
from sitemap import regenerate_full_sitemap

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_FILE = BASE_DIR / "manifest.json"

SITE = "https://insightginie.com"
POST_API = f"{SITE}/wp-json/wp/v2/posts"

PER_PAGE = 100
POSTS_PER_PAGE = 100

def load_manifest():
    if MANIFEST_FILE.exists() and MANIFEST_FILE.stat().st_size > 0:
        try:
            with open(MANIFEST_FILE, encoding="utf-8") as f:
                manifest = json.load(f)
                return {
                    "latest_page": int(manifest.get("latest_page", 0)),
                    "last_synced_post_id": int(manifest.get("last_synced_post_id", 0)),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return {"latest_page": 0, "last_synced_post_id": 0}

def load_existing_posts_from_pages():
    page_dir = BASE_DIR / "page"
    if not page_dir.exists():
        return {}

    posts_by_slug = {}
    for file in sorted(page_dir.glob("*.json")):
        try:
            with open(file, encoding="utf-8") as f:
                page_data = json.load(f)
                if isinstance(page_data, dict):
                    for slug, post in page_data.items():
                        if isinstance(post, dict):
                            posts_by_slug[slug] = {
                                "slug": slug,
                                "title": post.get("title", ""),
                                "date": post.get("date", ""),
                                "excerpt": post.get("excerpt", ""),
                            }
        except json.JSONDecodeError:
            continue
    return posts_by_slug

def save_manifest(manifest):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

def sanitize(content):
    content = re.sub(r"<script.*?>.*?</script>", "", content, flags=re.DOTALL)
    content = content.replace("{%", "{% raw %}{%")
    content = content.replace("%}", "%}{% endraw %}")
    return content

def generate_sitemap(all_posts):
    if not all_posts:
        regenerate_full_sitemap([])
        return

    url_list = []
    for post in all_posts:
        url_list.append({"url": f"https://aloycwl.github.io/{post['slug']}", "lastmod": post["date"][:10]})
    total_pages = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for page_num in range(1, total_pages + 1):
        url_list.append({"url": f"https://aloycwl.github.io/page/{page_num}/", "lastmod": all_posts[0]["date"][:10]})
    regenerate_full_sitemap(url_list)

def render_page_files(all_posts):
    page_dir = BASE_DIR / "page"
    page_dir.mkdir(exist_ok=True)
    for child in page_dir.glob("*.json"):
        child.unlink()

    total_pages = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        page_posts = all_posts[start:start + POSTS_PER_PAGE]
        listing_posts = {
            post["slug"]: {
                "title": post["title"],
                "date": post["date"][:10] if len(post["date"]) > 10 else post["date"],
                "excerpt": post["excerpt"],
            }
            for post in page_posts
        }
        with open(page_dir / f"{page_num}.json", "w", encoding="utf-8") as f:
            json.dump(listing_posts, f)

def reset_sync_state():
    for folder in [BASE_DIR / "data", BASE_DIR / "page"]:
        folder.mkdir(exist_ok=True)
        for child in folder.iterdir():
            if child.is_dir():
                import shutil
                shutil.rmtree(child)
            else:
                child.unlink()
    if MANIFEST_FILE.exists():
        MANIFEST_FILE.unlink()

def sync(max_posts=None, full_resync=False):
    if full_resync:
        print("Running full resync: clearing local sync state...")
        reset_sync_state()

    manifest = load_manifest()
    last_id = manifest.get("last_synced_post_id", 0)
    posts_by_slug = load_existing_posts_from_pages()

    page = 1
    processed = 0
    stop = False
    max_id = last_id

    print(f"Starting sync. Last synced post ID: {last_id}")
    while True:
        url = f"{POST_API}?per_page={PER_PAGE}&page={page}&_embed&orderby=id&order=asc&status=publish"
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

            posts_by_slug[slug] = {"slug": slug, "title": title, "date": date, "excerpt": excerpt}
            with open(BASE_DIR / "data" / f"{slug}.json", "w", encoding="utf-8") as f:
                json.dump({"content": content, "img": image, "date": date[:10], "excerpt": excerpt, "title": title, "slug": slug}, f)

            max_id = max(max_id, post["id"])
            processed += 1
        if stop:
            break
        page += 1

    all_posts = sorted(posts_by_slug.values(), key=lambda x: x["date"], reverse=True)
    latest_page = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    render_page_files(all_posts)
    generate_sitemap(all_posts)
    save_manifest({"latest_page": latest_page, "last_synced_post_id": max_id})

    print(f"Done. Processed {processed} new posts. Total posts: {len(all_posts)}")

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
