import os
import requests
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "_data"
DATA_DIR.mkdir(exist_ok=True)

SITE = "https://insightginie.com"
CATEGORY_API = f"{SITE}/wp-json/wp/v2/categories"

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
                "id": c["id"],
                "slug": c["slug"],
                "name": c["name"],
                "parent": c["parent"]
            }
        page += 1
    return categories

def build_tree(categories):
    tree = {}

    # First pass: find all main categories (parent = 0)
    for c_id, c in categories.items():
        if c["parent"] == 0:
            tree[c["slug"]] = {
                "name": c["name"],
                "slug": c["slug"],
                "subcategories": []
            }

    # Second pass: attach subcategories
    for c_id, c in categories.items():
        if c["parent"] != 0:
            parent_id = c["parent"]
            if parent_id in categories:
                parent_slug = categories[parent_id]["slug"]
                if parent_slug in tree:
                    tree[parent_slug]["subcategories"].append({
                        "name": c["name"],
                        "slug": c["slug"]
                    })

    return tree

def generate_pages(tree):
    for main_slug, main_data in tree.items():
        main_dir = BASE_DIR / main_slug
        main_dir.mkdir(exist_ok=True)

        main_path = main_dir / "index.html"
        main_fm = {
            "layout": "category",
            "category": main_slug,
            "title": main_data["name"]
        }

        with open(main_path, "w", encoding="utf-8") as f:
            f.write(f"---\n{yaml.dump(main_fm, sort_keys=False)}---\n")

        for sub in main_data["subcategories"]:
            sub_slug = sub["slug"]
            sub_dir = main_dir / sub_slug
            sub_dir.mkdir(exist_ok=True)

            sub_path = sub_dir / "index.html"
            sub_fm = {
                "layout": "subcategory",
                "category": main_slug,
                "subcategory": sub_slug,
                "title": f"{main_data['name']} / {sub['name']}",
                "pagination": {
                    "enabled": True,
                    "category": f"{main_slug},{sub_slug}"
                }
            }

            with open(sub_path, "w", encoding="utf-8") as f:
                f.write(f"---\n{yaml.dump(sub_fm, sort_keys=False)}---\n")

def sync_categories():
    print("Fetching categories...")
    categories = fetch_categories()

    print("Building tree...")
    tree = build_tree(categories)

    print("Saving _data/categories.yml...")
    tree_list = list(tree.values())
    with open(DATA_DIR / "categories.yml", "w", encoding="utf-8") as f:
        yaml.dump(tree_list, f, sort_keys=False)

    print("Generating category pages...")
    generate_pages(tree)

    print("Done!")

if __name__ == "__main__":
    sync_categories()
