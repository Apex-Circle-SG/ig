const SITE_NAME = 'InsightGinie Archive';

const isPostPage = !!document.querySelector('article') && !document.querySelector('.post-list');
const isPageListing = !!document.querySelector('.post-list');
const isHomepage = !isPostPage && !isPageListing;

document.addEventListener('DOMContentLoaded', init);

async function init() {
  const [header, footer] = await Promise.all([
    fetch('/templates/header.html').then(r => r.text()),
    fetch('/templates/footer.html').then(r => r.text())
  ]);
  document.getElementById('site-header').innerHTML = header;
  document.getElementById('site-footer').innerHTML = footer;

  if (isHomepage) {
    const manifest = await fetch('/manifest.json').then(r => r.json());
    const latestPage = manifest.latest_page || 1;
    window.location.replace('/page/' + latestPage + '/');
    return;
  }

  enhanceDates();
}

function enhanceDates() {
  if (typeof dayjs === 'undefined') return;
  document.querySelectorAll('.post-date[data-date]').forEach(el => {
    el.textContent = dayjs(el.dataset.date).fromNow();
  });
}
