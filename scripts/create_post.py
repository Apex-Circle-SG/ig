#!/usr/bin/env python3
import os
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BUCKET_DIR = DATA_DIR / "buckets"
PENDING_DIR = DATA_DIR / "pending"

POSTS_PER_BUCKET = 100

# Initialize directories
for d in [DATA_DIR, BUCKET_DIR, PENDING_DIR]:
    d.mkdir(exist_ok=True)


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))


def get_index():
    return load_json(DATA_DIR / "index.json", {
        "total_posts": 0,
        "total_buckets": 0,
        "active_bucket": 1,
        "posts": []
    })


def save_index(index):
    save_json(DATA_DIR / "index.json", index)


def get_slugmap():
    return load_json(DATA_DIR / "slugmap.json", {})


def save_slugmap(slugmap):
    save_json(DATA_DIR / "slugmap.json", slugmap)


def get_bucket(bucket_num):
    bucket_path = BUCKET_DIR / f"{bucket_num:04d}.json"
    return load_json(bucket_path)


def save_bucket(bucket):
    bucket_path = BUCKET_DIR / f"{bucket['id']:04d}.json"
    save_json(bucket_path, bucket)


def get_active_bucket():
    index = get_index()
    active = get_bucket(index["active_bucket"])

    if not active:
        active = {
            "id": index["active_bucket"],
            "sealed": False,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "posts": []
        }

    return active


def save_active_bucket(bucket):
    if bucket["sealed"]:
        save_bucket(bucket)
    else:
        save_json(PENDING_DIR / "current.json", bucket)


def create_post(title, slug, date, content, author=None):
    """Create a new post - primary public interface"""
    index = get_index()
    slugmap = get_slugmap()
    bucket = get_active_bucket()

    # Skip duplicate slugs
    if slug in slugmap:
        return False

    # New post object
    post = {
        "id": index["total_posts"] + 1,
        "slug": slug,
        "title": title,
        "date": date[:10],
        "content": content,
        "image": f"https://picsum.photos/id/{index['total_posts'] % 1084}/800/400"
    }

    # Insert at top (newest first)
    bucket["posts"].insert(0, post)
    index["posts"].insert(0, {
        "slug": slug,
        "bucket": bucket["id"],
        "date": post["date"]
    })

    slugmap[slug] = bucket["id"]
    index["total_posts"] += 1

    # Check if bucket is full and needs sealing
    if len(bucket["posts"]) >= POSTS_PER_BUCKET:
        bucket["sealed"] = True
        save_bucket(bucket)

        # Create new empty active bucket
        index["active_bucket"] += 1
        index["total_buckets"] += 1
        new_bucket = {
            "id": index["active_bucket"],
            "sealed": False,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "posts": []
        }
        save_active_bucket(new_bucket)
    else:
        save_active_bucket(bucket)

    save_index(index)
    save_slugmap(slugmap)

    return True


def seal_current_bucket():
    """Manually seal active bucket before it reaches 100 posts"""
    index = get_index()
    bucket = get_active_bucket()
    bucket["sealed"] = True
    save_bucket(bucket)

    index["active_bucket"] += 1
    index["total_buckets"] += 1
    new_bucket = {
        "id": index["active_bucket"],
        "sealed": False,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "posts": []
    }

    save_active_bucket(new_bucket)
    save_index(index)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "seal":
        seal_current_bucket()
        print("Bucket sealed")
