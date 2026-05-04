from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:8000')
    page.wait_for_selector('img.post-thumb')
    page.evaluate('''() => {
        const images = Array.from(document.querySelectorAll('img.post-thumb'));
        return Promise.all(images.map(img => {
            if (img.complete) return Promise.resolve();
            return new Promise(resolve => {
                img.onload = resolve;
                img.onerror = resolve;
            });
        }));
    }''')
    page.screenshot(path='homepage_v2.png', full_page=True)

    # Test route parameter bug fix
    page.goto('http://localhost:8000/?route=dont-break-the-bank-on-bots-10-savvy-ways-to-optimise-your-ai-costs')
    page.wait_for_selector('article h1')

    # Verify the URL was rewritten properly without the ?route parameter in the pathname history
    current_url = page.url
    print("URL after load:", current_url)

    page.screenshot(path='post_v2.png')

    browser.close()
