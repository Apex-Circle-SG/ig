#!/usr/bin/env python3
import os
from datetime import datetime
from pathlib import Path
from memory import memory

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BUCKET_DIR = DATA_DIR / "buckets"
PENDING_DIR = DATA_DIR / "pending"

POSTS_PER_BUCKET = 100

# Initialize directories
for d in [DATA_DIR, BUCKET_DIR, PENDING_DIR]:
    d.mkdir(exist_ok=True, parents=True)


def get_index():
    return memory.load(str(DATA_DIR / "index.json"), {
        "total_posts": 0,
        "total_buckets": 0,
        "active_bucket": 1,
        "posts": []
    })


def save_index(index):
    memory.save(str(DATA_DIR / "index.json"), index)


def get_slugmap():
    return memory.load(str(DATA_DIR / "slugmap.json"), {})


def save_slugmap(slugmap):
    memory.save(str(DATA_DIR / "slugmap.json"), slugmap)


def get_bucket(bucket_num):
    bucket_path = BUCKET_DIR / f"{bucket_num:04d}.json"
    return memory.load(str(bucket_path))


def save_bucket(bucket):
    bucket_path = BUCKET_DIR / f"{bucket['id']:04d}.json"
    memory.save(str(bucket_path), bucket)


def get_active_bucket():
    index = get_index()
    active = get_bucket(index["active_bucket"])

    # If bucket is already sealed, skip pending file
    if active and active["sealed"]:
        active = None
    
    # Load pending only if bucket is not sealed yet
    if not active:
        pending_path = PENDING_DIR / "current.json"
        active = memory.load(str(pending_path))
        
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
        # Delete pending file when bucket is sealed
        pending_file = PENDING_DIR / "current.json"
        if pending_file.exists():
            pending_file.unlink()
    else:
        memory.save(str(PENDING_DIR / "current.json"), bucket)


def create_post(title, slug, date, content, author=None):
    """Create a new post - primary public interface"""

    with memory.transaction() as tx:
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

        if author:
            post["author"] = author

        # Insert at top (newest first)
        bucket["posts"].insert(0, post)
        index["posts"].insert(0, {
            "slug": slug,
            "bucket": bucket["id"],
            "date": post["date"]
        })

        slugmap[slug] = bucket["id"]
        index["total_posts"] += 1

        # Fixed: Exact match for 100 posts
        if len(bucket["posts"]) == POSTS_PER_BUCKET:
            bucket["sealed"] = True
            tx.set(str(BUCKET_DIR / f"{bucket['id']:04d}.json"), bucket)

            # Create new empty active bucket
            index["active_bucket"] += 1
            index["total_buckets"] += 1
            new_bucket = {
                "id": index["active_bucket"],
                "sealed": False,
                "created": datetime.now().strftime("%Y-%m-%d"),
                "posts": []
            }
            tx.set(str(PENDING_DIR / "current.json"), new_bucket)
        else:
            tx.set(str(PENDING_DIR / "current.json"), bucket)

        tx.set(str(DATA_DIR / "index.json"), index)
        tx.set(str(DATA_DIR / "slugmap.json"), slugmap)

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
