# Plan: Fix SEO Meta Description & Social Open Graph Tags

## Status: Planned

## Issues
1.  Post meta descriptions are missing - all posts share the same site-wide description
2.  No Open Graph (OG) images are being shown when sharing on LinkedIn, Twitter, Facebook
3.  `featured_image` exists in every post frontmatter but is not used by the SEO plugin
4.  Link previews are generic and non-functional for promotion purposes

## Required Changes

### 1. Update sync_wordpress.py
- Add proper `description` field to post frontmatter using post excerpt
- Add proper `image` field alias that jekyll-seo-tag recognizes
- Keep existing `featured_image` for backwards compatibility

### 2. Update default.html layout
- Explicitly add Open Graph / Twitter Card meta tags
- Override the default SEO plugin behavior for image tags
- Ensure proper 1200x630 aspect ratio for social previews
- Set correct card type for Twitter

### 3. Verify jekyll-seo-tag configuration
- Confirm plugin is correctly configured to use post images
- Add required site properties for social media

## Result
After implementation:
✅ Each post will have its own unique meta description
✅ LinkedIn/Twitter/Facebook will display correct post thumbnail previews
✅ Posts will show proper titles, descriptions and images when shared
✅ SEO score will improve significantly
✅ Link previews will work correctly for promotion purposes

## Files affected:
- `/home/openclaw/ig/scripts/sync_wordpress.py`
- `/home/openclaw/ig/_layouts/default.html`
- `/home/openclaw/ig/_config.yml` (if needed)
