import sys
import html as html_mod
import requests
import json
import re
from pathlib import Path
from sitemap import batch_append_sitemap
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_FILE = BASE_DIR / "manifest.json"
POSTS_DIR = BASE_DIR / "posts"
PAGE_DIR = BASE_DIR / "page"
DATA_DIR = BASE_DIR / "data"

WP_SITE = "https://insightginie.com"
SITE_URL = "https://github.insightginie.com"
SITE_NAME = "InsightGinie Archive"
SITE_DESC = "News of Tomorrow"
POST_API = f"{WP_SITE}/wp-json/wp/v2/posts"

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
                    "last_api_page": int(manifest.get("last_api_page", 1)),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return {"latest_page": 0, "last_synced_post_id": 0, "last_api_page": 1}

def load_latest_page(latest_page_num):
    """Load only the latest page file to check how many posts it has."""
    if latest_page_num <= 0:
        return []
    page_file = PAGE_DIR / f"{latest_page_num}.json"
    if page_file.exists():
        try:
            with open(page_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            pass
    return []

def count_posts_in_page(page_num):
    """Quickly count posts in a page file without loading all data."""
    if page_num <= 0:
        return 0
    page_file = PAGE_DIR / f"{page_num}.json"
    if not page_file.exists():
        return 0
    try:
        with open(page_file, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
    except (json.JSONDecodeError, ValueError):
        pass
    return 0

def save_manifest(manifest):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

def sanitize(content):
    content = re.sub(r"<script.*?>.*?</script>", "", content, flags=re.DOTALL)
    content = content.replace("{%", "{% raw %}{%")
    content = content.replace("%}", "%}{% endraw %}")
    return content

def generate_post_html(title, slug, date, excerpt, content, image):
    date_iso = date[:10]
    post_url = f"{SITE_URL}/posts/{slug}/"
    og_image = image.replace("/800/400", "/1200/630") if "/800/400" in image else image
    esc = html_mod.escape
    clean_excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
    jsonld_article = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "datePublished": date_iso,
        "dateModified": date_iso,
        "image": [og_image],
        "description": clean_excerpt or SITE_DESC,
        "mainEntityOfPage": post_url,
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL
        }
    }, ensure_ascii=False)
    jsonld_breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": title, "item": post_url}
        ]
    }, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(clean_excerpt or SITE_DESC)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{post_url}">
<meta name="author" content="{SITE_NAME}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(clean_excerpt or SITE_DESC)}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{post_url}">
<meta property="og:locale" content="en_US">
<meta property="article:published_time" content="{date_iso}">
<meta property="article:modified_time" content="{date_iso}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(clean_excerpt or SITE_DESC)}">
<meta name="twitter:image" content="{og_image}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" type="image/png" href="https://fastly.picsum.photos/id/695/64/64.jpg?hmac=9e78jBXMmSJ38MUvNXDQKWoN0KrAVf9CwfYXlYVxY2s">
<script type="application/ld+json">{jsonld_article}</script>
<script type="application/ld+json">{jsonld_breadcrumb}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../assets/styles.css">
</head>
<body>
<div id="site-header"></div>
<main class="container">
<article>
<h1>{title}</h1>
<time datetime="{date_iso}" style="color:#718096; font-size:0.9rem;">{date_iso}</time>
<img src="{image}" style="width:100%; margin: 1rem 0; border-radius: 4px;" alt="{esc(title)}">
{content}
</article>
<div class="pagination"><a href="../../" class="button">&laquo; Back to archive</a></div>
</main>
<div id="site-footer"></div>
<script src="../../assets/app.js"></script>
</body>
</html>
'''

def append_to_existing_page(page_num, new_posts):
    """Append new posts to an existing page file."""
    PAGE_DIR.mkdir(exist_ok=True)
    page_file = PAGE_DIR / f"{page_num}.json"
    
    # Load existing posts
    existing = []
    if page_file.exists():
        try:
            with open(page_file, encoding="utf-8") as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
        except (json.JSONDecodeError, ValueError):
            existing = []
    
    # Append new posts and sort by date (newest first)
    combined = existing + new_posts
    combined.sort(key=lambda x: x["date"], reverse=True)
    
    with open(page_file, "w", encoding="utf-8") as f:
        json.dump(combined, f)
    
    return len(combined)

def create_new_page(page_num, posts):
    """Create a new page file."""
    PAGE_DIR.mkdir(exist_ok=True)
    page_file = PAGE_DIR / f"{page_num}.json"
    
    # Sort by date (newest first)
    sorted_posts = sorted(posts, key=lambda x: x["date"], reverse=True)
    
    with open(page_file, "w", encoding="utf-8") as f:
        json.dump(sorted_posts, f)

def sync(max_posts=None, full_resync=False):
    if full_resync:
        print("Running full resync: clearing local sync state...")
        import shutil
        for folder in [POSTS_DIR, PAGE_DIR, DATA_DIR]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(exist_ok=True)
        sitemap_file = BASE_DIR / "sitemap.xml"
        if sitemap_file.exists():
            sitemap_file.unlink()
        if MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()

    manifest = load_manifest()
    last_id = manifest.get("last_synced_post_id", 0)
    latest_page = manifest.get("latest_page", 0)
    last_api_page = manifest.get("last_api_page", 1)
    
    current_page_count = count_posts_in_page(latest_page) if latest_page > 0 else 0
    
    processed = 0
    stop = False
    max_id = last_id
    
    if full_resync:
        page = 1
    else:
        page = max(1, last_api_page - 1)
    print(f"Starting API page: {page}, last_api_page: {last_api_page}, latest_page: {latest_page}")
    
    # Track posts for the current page being filled
    posts_for_current_page = []
    current_page_num = latest_page if latest_page > 0 else 1
    current_page_post_count = current_page_count
    
    # Collect sitemap entries for batch update at the end
    sitemap_entries = []
    
    # CRITICAL FIX: If resuming and the current page is already full, move to next page
    # This prevents overwriting existing full pages when resuming sync
    if current_page_post_count >= POSTS_PER_PAGE and not full_resync:
        print(f"Page {current_page_num} is full ({current_page_post_count} posts). Moving to next page.")
        current_page_num += 1
        current_page_post_count = count_posts_in_page(current_page_num)
        # Keep incrementing until we find a page with space
        while current_page_post_count >= POSTS_PER_PAGE:
            print(f"Page {current_page_num} is also full. Moving to next page.")
            current_page_num += 1
            current_page_post_count = count_posts_in_page(current_page_num)
        latest_page = current_page_num - 1
    
    print(f"Starting sync. Last synced post ID: {last_id}, Current page: {current_page_num}, Current page has {current_page_post_count} posts")

    try:
        while True:
            url = f"{POST_API}?per_page={PER_PAGE}&page={page}&_embed&orderby=id&order=asc&status=publish"
            r = session.get(url, timeout=60)
            if r.status_code != 200:
                break
            posts = r.json()
            if not posts:
                break

            new_in_page = 0
            for post in posts:
                if max_posts is not None and processed >= max_posts:
                    stop = True
                    break

                slug = post["slug"]
                post_dir = POSTS_DIR / slug
                if (post_dir / "index.html").exists():
                    continue
                new_in_page += 1

                title = post["title"]["rendered"]
                print(f"synced: [{slug}] {title}")
                date = post["date_gmt"] + "+00:00"
                content = sanitize(post["content"]["rendered"])
                excerpt = re.sub(r'<[^>]+>', '', post.get("excerpt", {}).get("rendered", "")).strip()[:160]
                image = f"https://picsum.photos/seed/{slug}/800/400"

                POSTS_DIR.mkdir(exist_ok=True)
                post_dir.mkdir(exist_ok=True)
                with open(post_dir / "index.html", "w", encoding="utf-8") as f:
                    f.write(generate_post_html(title, slug, date, excerpt, content, image))

                sitemap_entries.append({
                    'url': f"{SITE_URL}/posts/{slug}/",
                    'lastmod': date[:10],
                    'priority': '0.8'
                })

                # Prepare post data for page
                post_data = {
                    "id": post["id"],
                    "slug": slug,
                    "title": title,
                    "date": date,
                    "excerpt": excerpt,
                }

                # Add to current page being built
                posts_for_current_page.append(post_data)
                current_page_post_count += 1
                
                # Check if current page is now full
                if current_page_post_count >= POSTS_PER_PAGE:
                    # Save the full page
                    if current_page_num == latest_page and not full_resync:
                        # If we're filling the existing latest page (not new), use append mode
                        # But since we just filled it completely, we can just overwrite
                        create_new_page(current_page_num, posts_for_current_page)
                    else:
                        create_new_page(current_page_num, posts_for_current_page)
                    
                    print(f"Saved page {current_page_num} with {len(posts_for_current_page)} posts")
                    
                    # Move to next page
                    current_page_num += 1
                    posts_for_current_page = []
                    current_page_post_count = 0
                    
                    # Update latest_page tracking
                    latest_page = current_page_num - 1
                    
                    # Save manifest after each page file write (as requested for safety)
                    save_manifest({"latest_page": latest_page, "last_synced_post_id": post["id"], "last_api_page": page})
                else:
                    # Page not full yet, just update manifest with progress
                    # (still save manifest for resume capability)
                    save_manifest({"latest_page": current_page_num, "last_synced_post_id": post["id"], "last_api_page": page})

                max_id = max(max_id, post["id"])
                processed += 1

            if stop:
                break
            
            # Early exit: if we're past the last known API page and got zero new posts,
            # we've caught up — no need to fetch more pages
            if new_in_page == 0 and page > last_api_page:
                print(f"No new posts on API page {page} (past last_api_page {last_api_page}). Stopping.")
                break
            page += 1
            
    except (KeyboardInterrupt, Exception) as e:
        print(f"\nSync interrupted or failed: {e}")
        print("Saving partial progress...")
    finally:
        # Save any remaining posts in the current page (partial page)
        if posts_for_current_page:
            if current_page_num == latest_page and not full_resync:
                # Append to existing latest page
                append_to_existing_page(current_page_num, posts_for_current_page)
            else:
                create_new_page(current_page_num, posts_for_current_page)
            print(f"Saved final partial page {current_page_num} with {len(posts_for_current_page)} posts")
        
        # Batch update sitemap with all new entries at once (much faster than per-post updates)
        if sitemap_entries:
            print(f"Updating sitemap with {len(sitemap_entries)} new entries...")
            batch_append_sitemap(sitemap_entries)
        
        # Final manifest save
        save_manifest({"latest_page": current_page_num if posts_for_current_page else current_page_num - 1, "last_synced_post_id": max_id, "last_api_page": page})
        print(f"Done. Processed {processed} new posts. Latest page: {current_page_num}")

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
