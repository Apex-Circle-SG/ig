import os
import requests
import yaml
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent
POST_DIR = BASE_DIR / "_posts"
MEDIA_DIR = BASE_DIR / "media/images"
STATE_FILE = BASE_DIR / "scripts/last_sync.json"
POST_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

SITE = "https://insightginie.com"

POST_API = f"{SITE}/wp-json/wp/v2/posts"
CATEGORY_API = f"{SITE}/wp-json/wp/v2/categories"

PER_PAGE = 100
MAX_WORKERS = 10

Path(POST_DIR).mkdir(exist_ok=True)
Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)


# -----------------------------
# Load sync state
# -----------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_id": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# -----------------------------
# Fetch categories
# -----------------------------

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

            categories[c["id"]] = {
                "slug": c["slug"],
                "parent": c["parent"]
            }

        page += 1

    return categories


def resolve_category(cat_id, categories):

    path = []

    while cat_id in categories:

        c = categories[cat_id]

        path.append(c["slug"])

        if c["parent"] == 0:
            break

        cat_id = c["parent"]

    path.reverse()

    return path


# -----------------------------
# Download image
# -----------------------------

def download_image(url):

    filename = url.split("/")[-1]

    local_path = f"{MEDIA_DIR}/{filename}"

    if os.path.exists(local_path):
        return f"/media/images/{filename}"

    try:

        img = requests.get(url, timeout=30)

        if img.status_code == 200:

            with open(local_path, "wb") as f:
                f.write(img.content)

            return f"/media/images/{filename}"

    except Exception:
        pass

    return None


# -----------------------------
# Clean content
# -----------------------------

def sanitize(content):

    content = re.sub(
        r"<script.*?>.*?</script>",
        "",
        content,
        flags=re.DOTALL
    )

    content = content.replace("{%", "{% raw %}{%")
    content = content.replace("%}", "%}{% endraw %}")

    return content


# -----------------------------
# Save post
# -----------------------------

def save_post(post, categories, executor):

    title = post["title"]["rendered"]
    slug = post["slug"]

    date = post["date_gmt"] + "+00:00"
    content = post["content"]["rendered"]

    content = sanitize(content)

    original_url = post["link"]

    media_url = None

    if "_embedded" in post:

        media = post["_embedded"].get("wp:featuredmedia")

        if media:
            media_url = media[0]["source_url"]

    media_path = None

    if media_url:

        future = executor.submit(download_image, media_url)

        media_path = future.result()

    cats = post["categories"]

    if cats:

        cat_path = resolve_category(cats[0], categories)

    else:

        cat_path = ["uncategorized"]

    folder = os.path.join(POST_DIR, *cat_path)

    Path(folder).mkdir(parents=True, exist_ok=True)

    filename = f"{date[:10]}-{slug}.md"

    path = os.path.join(folder, filename)

    frontmatter = {
        "layout": "post",
        "title": title,
        "date": date,
        "categories": cat_path,
        "original_url": original_url
    }

    if media_path:
        frontmatter["featured_image"] = media_path

    fm = yaml.dump(frontmatter, sort_keys=False)

    text = f"---\n{fm}---\n\n{content}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print("saved:", slug)


# -----------------------------
# Sync posts
# -----------------------------

def sync():

    state = load_state()

    last_id = state.get("last_id", 0)

    categories = fetch_categories()

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    page = 1

    while True:

        url = f"{POST_API}?per_page={PER_PAGE}&page={page}&_embed&orderby=id&order=desc&status=publish"

        r = requests.get(url)

        if r.status_code != 200:
            break

        posts = r.json()

        if not posts:
            break

        stop = False

        max_id = last_id

        for post in posts:

            if post["id"] <= last_id:
                stop = True
                break

            save_post(post, categories, executor)

            if post["id"] > max_id:
                max_id = post["id"]

        if stop:
            break

        page += 1

    state["last_id"] = max_id

    save_state(state)

# -----------------------------
# Run
# -----------------------------

if __name__ == "__main__":

    sync()