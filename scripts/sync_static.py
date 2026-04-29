import os
import sys
import requests
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "ig"
STATE_FILE = BASE_DIR / "scripts/last_sync.json"
PUBLIC_DIR.mkdir(exist_ok=True)

SITE = "https://insightginie.com"
POST_API = f"{SITE}/wp-json/wp/v2/posts"
CATEGORY_API = f"{SITE}/wp-json/wp/v2/categories"

PER_PAGE = 100
MAX_WORKERS = 10
POSTS_PER_PAGE = 100

HEAD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://aloycwl.github.io/ig/{slug}">
    {og_image}
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="https://aloycwl.github.io/ig/{slug}">
    <style>
        :root {{ color-scheme: light; }}
        body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #111; background: #fff; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 1rem; }}
        header {{ border-bottom: 1px solid #eee; padding-bottom: 1rem; margin-bottom: 2rem; }}
        header a {{ color: #111; text-decoration: none; font-weight: 600; font-size: 1.25rem; }}
        img {{ max-width: 100%; height: auto; border-radius: 4px; }}
        a {{ color: #0b57d0; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .post-list {{ list-style: none; padding: 0; }}
        .post-item {{ padding: 0.75rem 0; border-bottom: 1px solid #f5f5f5; }}
        .post-title {{ font-size: 1.1rem; font-weight: 500; }}
        .post-date {{ font-size: 0.85rem; color: #718096; margin-top: 0.25rem; display: block; }}
        .pagination {{ display: flex; justify-content: center; gap: 1rem; margin-top: 2rem; padding: 1rem; }}
        .pagination a {{ padding: 0.5rem 1rem; border-radius: 4px; background: #edf2f7; color: #2d3748; }}
        .footer {{ margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #eee; text-align: center; color: #718096; font-size: 0.9rem; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <a href="/ig/">InsightGinie Archive</a>
    </header>
"""

FOOTER_TEMPLATE = """
    <div class="footer">
        <p>Official site: <a href="https://insightginie.com">insightginie.com</a></p>
        <p>This is a public mirror archive.</p>
    </div>
</div>
</body>
</html>
"""


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_id": 0, "posts": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def fetch_categories():
    categories = {}
    page = 1
    while True:
        r = requests.get(f"{CATEGORY_API}?per_page=100&page={page}")
        if r.status_code != 200:
            break
        data = r.json()
        if not data:
            break
        for c in data:
            categories[c["id"]] = {"slug": c["slug"], "parent": c["parent"]}
        page += 1
    return categories


def sanitize(content):
    content = re.sub(r"<script.*?>.*?</script>", "", content, flags=re.DOTALL)
    content = content.replace("{%", "{% raw %}{%")
    content = content.replace("%}", "%}{% endraw %}")
    return content


def render_post(post):
    title = post["title"]["rendered"]
    slug = post["slug"]
    date = post["date_gmt"] + "+00:00"
    content = post["content"]["rendered"]
    content = sanitize(content)
    excerpt = post.get("excerpt", {}).get("rendered", "")
    excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()[:160]
    media_path = f"https://picsum.photos/1200/630?random={post['id']}"

    og_image = f'<meta property="og:image" content="{media_path}"><meta name="twitter:image" content="{media_path}">'

    html = HEAD_TEMPLATE.format(title=title, description=excerpt, slug=slug, og_image=og_image)
    html += f'<h1>{title}</h1>'
    html += f'<p style="color:#718096; font-size:0.9rem;">{date[:10]}</p>'
    html += content
    html += FOOTER_TEMPLATE

    with open(PUBLIC_DIR / f"{slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "id": post["id"],
        "slug": slug,
        "title": title,
        "date": date,
        "description": excerpt
    }


def render_index(all_posts):
    total = len(all_posts)
    pages = (total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    for page_num in range(1, pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        page_posts = all_posts[start:end]

        html = HEAD_TEMPLATE.format(
            title="InsightGinie Archive",
            description="News of Tomorrow",
            slug="",
            og_image=""
        )

        html += '<h1>InsightGinie Archive</h1><p style="color:#718096;">News of Tomorrow</p>'
        html += '<ul class="post-list">'

        for post in page_posts:
            html += f"""<li class="post-item">
                <a href="{post['slug']}.html" class="post-title">{post['title']}</a>
                <span class="post-date">{post['date'][:10]}</span>
            </li>"""

        html += '</ul>'

        if pages > 1:
            html += '<div class="pagination">'
            if page_num > 1:
                prev = 'index.html' if page_num == 2 else f'page-{page_num-1}.html'
                html += f'<a href="{prev}">&laquo; Previous</a>'
            html += f'<span>Page {page_num} / {pages}</span>'
            if page_num < pages:
                html += f'<a href="page-{page_num+1}.html">Next &raquo;</a>'
            html += '</div>'

        html += FOOTER_TEMPLATE

        filename = 'index.html' if page_num == 1 else f'page-{page_num}.html'
        with open(PUBLIC_DIR / filename, "w", encoding="utf-8") as f:
            f.write(html)


def sync(max_posts=None):
    state = load_state()
    last_id = state.get("last_id", 0)
    processed_posts = state.get("posts", {})
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    page = 1
    processed = 0
    stop = False
    max_id = last_id

    print(f"Starting sync. Last synced post ID: {last_id}")

    while True:
        url = f"{POST_API}?per_page={PER_PAGE}&page={page}&_embed&orderby=id&order=desc&status=publish"
        print(f"Fetching page {page}...")
        r = requests.get(url)
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

            print(f"Processing: {post['slug']}")
            post_data = render_post(post)
            processed_posts[str(post["id"])] = post_data

            if post["id"] > max_id:
                max_id = post["id"]

            processed += 1

        if stop:
            break
        page += 1

    print(f"Rendering index pages...")
    all_posts = sorted(processed_posts.values(), key=lambda x: x["date"], reverse=True)
    render_index(all_posts)

    if max_posts is None:
        state["last_id"] = max_id
        state["posts"] = processed_posts
        save_state(state)

    print(f"\nDone. Processed {processed} new posts. Total posts: {len(processed_posts)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        sync(int(sys.argv[1]))
    else:
        sync()
