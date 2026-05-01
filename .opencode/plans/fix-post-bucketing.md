# Fix: Post Bucketing Implementation Plan

## Overview
Remove unused static HTML file generation and integrate sync_static.py with the existing working bucket system that already stores posts correctly in numbered JSON folders with 100 posts per bucket.

---

## Changes Required

### 1. File: `/home/openclaw/ig/scripts/sync_static.py`

#### ✅ REMOVE:
- Line 11,12,13: `PUBLIC_DIR = BASE_DIR / "post"` and related directory creation
- Entire `render_post()` function (lines 66-142) - **this is the bug that dumps all html files**
- Line 380: `post_data = render_post(post)` call

#### ✅ ADD:
Import the bucket system functions at the top:
```python
from create_post import create_post, get_index
```

#### ✅ MODIFY line 379-381:
Replace:
```python
print(f"Processing: {post['slug']}")
post_data = render_post(post)
processed_posts[str(post["id"])] = post_data
```

With:
```python
print(f"Processing: {post['slug']}")
title = post["title"]["rendered"]
slug = post["slug"]
date = post["date_gmt"] + "+00:00"
content = post["content"]["rendered"]
content = sanitize(content)
excerpt = post.get("excerpt", {}).get("rendered", "")
excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()[:160]

# Save directly to bucket system (100 posts per numbered folder)
success = create_post(title, slug, date, content)

post_data = {
    "id": post["id"],
    "slug": slug,
    "title": title,
    "date": date,
    "description": excerpt
}
processed_posts[str(post["id"])] = post_data
```

---

## After Implementation Behavior

✅ **Posts will automatically be grouped:**
  - First 100 posts -> `/data/buckets/0001.json`
  - Next 100 posts -> `/data/buckets/0002.json`
  - Next 100 posts -> `/data/buckets/0003.json`
  - ...and so on automatically

✅ **NO HTML FILES CREATED ANYMORE**
✅ **Frontend continues to work EXACTLY THE SAME** - it already reads from these bucket files
✅ **No other changes required anywhere else**
✅ Your `/post/` folder will no longer be filled with thousands of individual files
✅ Storage usage will be drastically reduced (1 JSON file vs 100 HTML files)

---

## Verification Steps
1. Run `python3 scripts/sync_static.py`
2. Check `/data/buckets/` directory - you will see numbered json files
3. Count posts in each bucket - will be exactly 100 posts per bucket
4. Visit the site - all posts load normally, navigation works
5. Check `/post/` folder - no new files added there
