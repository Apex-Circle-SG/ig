import sys
import requests
import json
import re
from pathlib import Path
from sitemap import append_sitemap

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_FILE = BASE_DIR / "manifest.json"
DATA_DIR = BASE_DIR / "data"
PAGE_DIR = BASE_DIR / "page"

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
        for folder in [DATA_DIR, PAGE_DIR]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(exist_ok=True)
        # Clear sitemap too
        sitemap_file = BASE_DIR / "sitemap.xml"
        if sitemap_file.exists():
            sitemap_file.unlink()
        if MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()

    manifest = load_manifest()
    last_id = manifest.get("last_synced_post_id", 0)
    latest_page = manifest.get("latest_page", 0)
    
# Check how many posts are in the latest page
    current_page_count = count_posts_in_page(latest_page) if latest_page > 0 else 0
    
    page = 1
    processed = 0
    stop = False
    max_id = last_id
    
    # First, find which API page contains the last synced post
    # The manifest saves the last synced post ID, we need to find its page in the WP API
    # API pages are ordered by ID ascending: page 1 has oldest posts, higher pages have newer
    # Simply start from latest_page since new posts would be on later local pages
    page = latest_page  # Start from where local pages left off
    print(f"DEBUG: Starting API page: {page}, latest_page: {latest_page}")
    
    # Track posts for the current page being filled
    posts_for_current_page = []
    current_page_num = latest_page if latest_page > 0 else 1
    current_page_post_count = current_page_count
    
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
                    
                # CRITICAL FIX: Skip already-synced posts, don't stop entirely
                # The same page can contain both old and new posts in ascending order
                if post["id"] <= last_id:
                    # Skip this post but continue checking next post in same page
                    # print(f"Skipping post {post['id']} (already synced)")
                    continue

                title = post["title"]["rendered"]
                slug = post["slug"]
                print(f"synced: [{slug}] {title}")
                date = post["date_gmt"] + "+00:00"
                content = sanitize(post["content"]["rendered"])
                excerpt = re.sub(r'<[^>]+>', '', post.get("excerpt", {}).get("rendered", "")).strip()[:160]
                image = f"https://picsum.photos/seed/{slug}/800/400"

                # Save individual post data file
                DATA_DIR.mkdir(exist_ok=True)
                with open(DATA_DIR / f"{slug}.json", "w", encoding="utf-8") as f:
                    json.dump({"content": content, "img": image, "date": date[:10], "excerpt": excerpt, "title": title, "slug": slug}, f)

                # Append to sitemap immediately (O(1) operation using existing append_sitemap function)
                append_sitemap(f"https://aloycwl.github.io/{slug}", lastmod=date[:10])

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
                    save_manifest({"latest_page": latest_page, "last_synced_post_id": post["id"]})
                else:
                    # Page not full yet, just update manifest with progress
                    # (still save manifest for resume capability)
                    save_manifest({"latest_page": current_page_num, "last_synced_post_id": post["id"]})

                max_id = max(max_id, post["id"])
                processed += 1

            if stop:
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
        
        # Final manifest save
        save_manifest({"latest_page": current_page_num if posts_for_current_page else current_page_num - 1, "last_synced_post_id": max_id})
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
