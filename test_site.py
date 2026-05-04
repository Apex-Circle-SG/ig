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
    page.screenshot(path='homepage.png')
    browser.close()
