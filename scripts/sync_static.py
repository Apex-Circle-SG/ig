import os
import sys
import requests
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from sitemap import append_sitemap, regenerate_full_sitemap
from create_post import create_post

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "scripts/last_sync.json"

SITE = "https://insightginie.com"
POST_API = f"{SITE}/wp-json/wp/v2/posts"
CATEGORY_API = f"{SITE}/wp-json/wp/v2/categories"

PER_PAGE = 100
MAX_WORKERS = 10
POSTS_PER_PAGE = 100

# Load external templates - edit these files to change site design globally
with open(BASE_DIR / "templates/header.html", "r", encoding="utf-8") as f:
    HEAD_TEMPLATE = f.read()

with open(BASE_DIR / "templates/footer.html", "r", encoding="utf-8") as f:
    FOOTER_TEMPLATE = f.read()


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





def generate_sitemap(all_posts):
    url_list = []
    for post in all_posts:
        url_list.append({
            "url": f"https://aloycwl.github.io/{post['slug']}",
            "lastmod": post["date"][:10]
        })
    
    # Add all static pages
    total_pages = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for page_num in range(1, total_pages + 1):
        url_list.append({
            "url": f"https://aloycwl.github.io/page/{page_num}/",
            "lastmod": all_posts[0]["date"][:10] if page_num == total_pages else all_posts[(page_num-1)*POSTS_PER_PAGE]["date"][:10]
        })
    
    regenerate_full_sitemap(url_list)


def render_index(all_posts):
    total = len(all_posts)
    pages = (total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    # Create data directory
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)

    # Write master posts index
    master_index = []
    for i, post in enumerate(all_posts):
        master_index.append({
            "slug": post["slug"],
            "title": post["title"],
            "date": post["date"][:10],
            "page": (i // POSTS_PER_PAGE) + 1
        })

    with open(BASE_DIR / "posts.json", "w", encoding="utf-8") as f:
        json.dump(master_index, f)

    # Write batch data files and static page folders
    page_dir_base = BASE_DIR / "page"
    page_dir_base.mkdir(exist_ok=True)
    
    for page_num in range(1, pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        page_posts = all_posts[start:end]

        # Write json data
        with open(data_dir / f"{page_num}.json", "w", encoding="utf-8") as f:
            json.dump(page_posts, f)
        
        # Create static page directory (SEO permanent paths)
        page_dir = page_dir_base / str(page_num)
        page_dir.mkdir(exist_ok=True)
        
        # Only modify page index if it's the latest page (older pages are immutable)
        if page_num == pages or not os.path.exists(page_dir / "index.html"):
            # Generate static index.html for this page
            page_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>InsightGinie - Page {page}</title>
    <link rel="icon" type="image/jpeg" href="https://fastly.picsum.photos/id/695/64/64.jpg?hmac=9e78jBXMmSJ38MUvNXDQKWoN0KrAVf9CwfYXlYVxY2s">
    <script>window.location = "/?page={page}";</script>
    <noscript>
        <meta http-equiv="refresh" content="0; url=/?page={page}">
    </noscript>
</head>
<body>
    Redirecting...
</body>
</html>'''.format(page=page_num)
            
            with open(page_dir / "index.html", "w", encoding="utf-8") as f:
                f.write(page_html)

    # Write single root index.html
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>InsightGinie</title>
    <meta name="description" content="News of Tomorrow">
    <link rel="icon" type="image/png" href="https://fastly.picsum.photos/id/695/64/64.jpg?hmac=9e78jBXMmSJ38MUvNXDQKWoN0KrAVf9CwfYXlYVxY2s">
    <style>
        :root { color-scheme: light; }
        body { margin: 0; font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #111; background: #fff; }
        .container { max-width: 960px; margin: 0 auto; padding: 1rem; }
        header { border-bottom: 1px solid #eee; padding-bottom: 1rem; margin-bottom: 2rem; }
        header a { color: #111; text-decoration: none; font-weight: 600; font-size: 1.25rem; }
        img { max-width: 100%; height: auto; border-radius: 4px; }
        a { color: #0b57d0; text-decoration: none; cursor: pointer; }
        a:hover { text-decoration: underline; }
        .post-list { list-style: none; padding: 0; }
        .post-item { padding: 0.75rem 0; border-bottom: 1px solid #f5f5f5; }
        .post-title { font-size: 1.1rem; font-weight: 500; }
        .post-date { font-size: 0.85rem; color: #718096; margin-top: 0.25rem; display: block; }
        .pagination { display: flex; justify-content: center; gap: 1rem; margin-top: 2rem; padding: 1rem; }
        .pagination button { padding: 0.5rem 1rem; border-radius: 4px; background: #edf2f7; color: #2d3748; border: none; cursor: pointer; }
        .pagination button:disabled { opacity: 0.4; cursor: default; }
        .footer { margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #eee; text-align: center; color: #718096; font-size: 0.9rem; }
        #loading { text-align: center; padding: 2rem; }
    </style>
</head>
<body>
<div id="site-header"></div>
<div class="container">
    <div id="loading">Loading...</div>
    <div id="content"></div>
    <div id="pagination" class="pagination"></div>
</div>
<div id="site-footer"></div>

<script>
let allPosts = [];
let currentPage = 1;
let totalPages = 1;
const POSTS_PER_PAGE = 100;

document.addEventListener('DOMContentLoaded', init);

async function init() {
    allPosts = await fetch('/posts.json').then(r => r.json());
    totalPages = Math.ceil(allPosts.length / POSTS_PER_PAGE);
    currentPage = totalPages; // Always start on newest page

    const [header, footer] = await Promise.all([
        fetch('/templates/header.html').then(r => r.text()),
        fetch('/templates/footer.html').then(r => r.text())
    ]);
    document.getElementById('site-header').innerHTML = header;
    document.getElementById('site-footer').innerHTML = footer;

    window.addEventListener('popstate', handleRoute);
    handleRoute();
}

async function handleRoute() {
    const path = window.location.pathname.slice(1);

    if (!path || path === 'index.html') {
        renderPage(currentPage);
    } else {
        renderPost(path);
    }
}

async function renderPage(pageNum) {
    currentPage = pageNum;
    const posts = await fetch(`/data/${pageNum}.json`).then(r => r.json());

    let html = '<h1>InsightGinie Archive</h1><p style="color:#718096;">News of Tomorrow</p><ul class="post-list">';

    for (const post of posts) {
        html += `<li class="post-item">
            <a onclick="navigate('${post.slug}'); return false;" class="post-title">${post.title}</a>
            <span class="post-date">${post.date.slice(0,10)}</span>
        </li>`;
    }

    html += '</ul>';
    document.getElementById('content').innerHTML = html;

    let phtml = '';
    if (currentPage > 1) phtml += `<button onclick="renderPage(${currentPage-1})">&laquo; Previous</button>`;
    phtml += `<span>Page ${currentPage} / ${totalPages}</span>`;
    if (currentPage < totalPages) phtml += `<button onclick="renderPage(${currentPage+1})">Next &raquo;</button>`;
    document.getElementById('pagination').innerHTML = phtml;
}

async function renderPost(slug) {
    const postMeta = allPosts.find(p => p.slug === slug);
    if (!postMeta) { renderPage(totalPages); return; }

    const posts = await fetch(`/data/${postMeta.page}.json`).then(r => r.json());
    const post = posts.find(p => p.slug === slug);

    document.getElementById('content').innerHTML = `
        <h1>${post.title}</h1>
        <p style="color:#718096; font-size:0.9rem;">${post.date.slice(0,10)}</p>
        ${post.content}
    `;
    document.getElementById('pagination').innerHTML = `<button onclick="navigate(''); return false;">&laquo; Back to archive</button>`;
}

function navigate(slug) {
    const url = '/' + slug;
    history.pushState(null, '', url);
    handleRoute();
}
</script>
</body>
</html>'''

    with open(BASE_DIR / "index.html", "w", encoding="utf-8") as f:
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
            title = post["title"]["rendered"]
            slug = post["slug"]
            date = post["date_gmt"] + "+00:00"
            content = post["content"]["rendered"]
            content = sanitize(content)
            excerpt = post.get("excerpt", {}).get("rendered", "")
            excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()[:160]
            
            # Save post directly to bucket system (100 posts per numbered folder)
            create_post(title, slug, date, content)
            
            post_data = {
                "id": post["id"],
                "slug": slug,
                "title": title,
                "date": date,
                "description": excerpt
            }
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
    generate_sitemap(all_posts)

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
