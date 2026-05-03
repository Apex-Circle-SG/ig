import json
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def load_posts_index():
    all_posts = []
    page_dir = BASE_DIR / "page"
    if page_dir.exists():
        for file in sorted(page_dir.glob("*.json"), key=lambda x: int(x.stem)):
            try:
                with open(file, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_posts.extend(data)
            except (json.JSONDecodeError, ValueError):
                pass
    return all_posts

def get_base_html():
    with open(BASE_DIR / "index.html", "r", encoding="utf-8") as f:
        return f.read()

def generate_pages():
    posts = load_posts_index()
    base_html = get_base_html()

    print(f"Generating static HTML for {len(posts)} posts for SEO...")

    for post in posts:
        slug = post.get("slug")
        if not slug:
            continue

        # Create directory for the slug
        post_dir = BASE_DIR / slug
        post_dir.mkdir(exist_ok=True)

        # We need the full post data for the image
        post_image = f"https://picsum.photos/seed/{slug}/1200/630"
        try:
            with open(BASE_DIR / "data" / f"{slug}.json", "r", encoding="utf-8") as f:
                full_post = json.load(f)
                post_image = full_post.get("img", post_image)
        except Exception:
            pass

        title = post.get("title", "InsightGinie")
        excerpt = post.get("excerpt", "News of Tomorrow").replace('"', '&quot;')
        url = f"https://aloycwl.github.io/ig/{slug}"

        # Replace meta tags in base html
        html = base_html

        # Update Titles
        html = html.replace('<title>InsightGinie - News of Tomorrow</title>', f'<title>{title} - InsightGinie</title>')
        html = html.replace('<meta name="title" content="InsightGinie - News of Tomorrow">', f'<meta name="title" content="{title}">')
        html = html.replace('<meta property="og:title" content="InsightGinie - News of Tomorrow">', f'<meta property="og:title" content="{title}">')
        html = html.replace('<meta property="twitter:title" content="InsightGinie - News of Tomorrow">', f'<meta property="twitter:title" content="{title}">')

        # Update Descriptions
        html = html.replace('<meta name="description" content="Discover the latest insights, news, and analysis on AI, Business, Finance, Tech, and more at InsightGinie.">', f'<meta name="description" content="{excerpt}">')
        html = html.replace('<meta property="og:description" content="Discover the latest insights, news, and analysis on AI, Business, Finance, Tech, and more at InsightGinie.">', f'<meta property="og:description" content="{excerpt}">')
        html = html.replace('<meta property="twitter:description" content="Discover the latest insights, news, and analysis on AI, Business, Finance, Tech, and more at InsightGinie.">', f'<meta property="twitter:description" content="{excerpt}">')

        # Update Image
        html = html.replace('<meta property="og:image" content="https://picsum.photos/id/695/1200/630">', f'<meta property="og:image" content="{post_image}">')
        html = html.replace('<meta property="twitter:image" content="https://picsum.photos/id/695/1200/630">', f'<meta property="twitter:image" content="{post_image}">')

        # Update URL
        html = html.replace('<meta property="og:url" content="https://aloycwl.github.io/ig/">', f'<meta property="og:url" content="{url}">')
        html = html.replace('<meta property="twitter:url" content="https://aloycwl.github.io/ig/">', f'<meta property="twitter:url" content="{url}">')
        html = html.replace('<link rel="canonical" href="https://aloycwl.github.io/ig/">', f'<link rel="canonical" href="{url}">')

        # Update JSON-LD
        json_ld = {
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": title,
          "image": [post_image],
          "description": excerpt,
          "mainEntityOfPage": url,
          "author": {
             "@type": "Organization",
             "name": "InsightGinie"
          }
        }

        # Replace the default JSON-LD block
        import re
        json_ld_str = json.dumps(json_ld, indent=4).replace('\\', '\\\\') # escape backslashes for re.sub
        html = re.sub(
            r'<script type="application/ld\+json" id="jsonld-site">.*?</script>',
            f'<script type="application/ld+json" id="jsonld-site">\n{json_ld_str}\n    </script>',
            html,
            flags=re.DOTALL
        )

        # Adjust base paths so CSS/JS load correctly from subdirectories
        html = html.replace('href="./assets/', 'href="../assets/')
        html = html.replace('src="./assets/', 'src="../assets/')

        with open(post_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)

    print("Done generating SEO pages.")

if __name__ == "__main__":
    generate_pages()
