import os
import yaml
from pathlib import Path
from collections import defaultdict

POST_DIR = "../_posts"
CATEGORY_DIR = "../categories"
SUBCATEGORY_DIR = "../subcategories"

Path(CATEGORY_DIR).mkdir(exist_ok=True)
Path(SUBCATEGORY_DIR).mkdir(exist_ok=True)

categories = defaultdict(set)


def extract_frontmatter(path):

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.startswith("---"):
        return None

    parts = text.split("---")

    if len(parts) < 3:
        return None

    return yaml.safe_load(parts[1])


def scan_posts():

    for root, dirs, files in os.walk(POST_DIR):

        for file in files:

            if not file.endswith(".md"):
                continue

            path = os.path.join(root, file)

            fm = extract_frontmatter(path)

            if not fm:
                continue

            cats = fm.get("categories", [])

            if not cats:
                continue

            main = cats[0]

            if len(cats) > 1:
                sub = cats[1]
                categories[main].add(sub)
            else:
                categories[main]


def create_category_pages():

    for main in sorted(categories.keys()):

        path = os.path.join(CATEGORY_DIR, f"{main}.md")

        content = f"""---
layout: category
category: {main}
permalink: /categories/{main}/
title: {main.capitalize()}
---
"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        print("category:", main)


def create_subcategory_pages():

    for main, subs in categories.items():

        for sub in sorted(subs):

            path = os.path.join(SUBCATEGORY_DIR, f"{main}-{sub}.md")

            content = f"""---
layout: subcategory
category: {main}
subcategory: {sub}
permalink: /{main}/{sub}/
title: {sub.capitalize()}
---
"""

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            print("subcategory:", main, "/", sub)


def main():

    scan_posts()

    create_category_pages()

    create_subcategory_pages()

    print("done.")


if __name__ == "__main__":
    main()