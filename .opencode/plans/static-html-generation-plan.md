# Plan: Remove Jekyll completely. Generate 100% static HTML directly from sync script

## Why this is 100x better:
✅ No Jekyll, no gems, no build errors, no plugin limitations
✅ No Github Pages hidden magic or restrictions
✅ Everything runs locally on your machine
✅ Full control over every single pixel, URL and behavior
✅ Sync script generates final static HTML files that Github Pages just serves as-is
✅ No waiting for builds, no debugging CI failures
✅ Pagination, indexes, navigation all generated exactly how you want it

## Architecture Overview:
The sync_wordpress.py will become a full static site generator:

1. Fetch posts from WordPress API
2. Render each post as standalone HTML file
3. Generate main index page with post listing
4. Generate pagination pages (page/2, page/3 etc)
5. Generate sitemap.xml, robots.txt
6. All files are written directly to output folder
7. You just git commit and push - Github Pages does NOT process anything

## Advantages over Jekyll:
- Posts are immediately visible with zero delay
- No future date issues
- No pagination plugins
- Full control over OG tags, meta, SEO
- Exactly matching URLs `aloycwl.github.io/ig/[slug-name]`
- No build step required
- No Ruby dependencies
- Works on every operating system

## Implementation Steps:
1. Modify sync script to output pure HTML instead of markdown
2. Add simple HTML template for posts
3. Add index page generation
4. Add pagination generation
5. Remove all Jekyll related files
6. No more _posts folder, _layouts, _config.yml etc

## Output structure:
```
/ig/index.html          <- main index page
/ig/page/2/index.html   <- page 2
/ig/page/3/index.html   <- page 3
/ig/post-slug.html      <- individual posts
/ig/sitemap.xml
/ig/robots.txt
```

This will work flawlessly forever. No more issues.

Should I proceed with implementing this design?
