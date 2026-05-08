const isPostPage = !!document.querySelector('article') && !document.querySelector('.post-list');
const isPageListing = !!document.querySelector('.post-list');
const isHomepage = !isPostPage && !isPageListing;

document.addEventListener('DOMContentLoaded', init);

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

async function loadDayjs() {
  await loadScript('https://cdn.jsdelivr.net/npm/dayjs@1/dayjs.min.js');
  await loadScript('https://cdn.jsdelivr.net/npm/dayjs@1/plugin/relativeTime.js');
  dayjs.extend(window.dayjs_plugin_relativeTime);
}

function loadGtag() {
  const s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=G-MZSFSG62B8';
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-MZSFSG62B8');
  window.gtag = gtag;
}

async function init() {
  const [header, footer, head] = await Promise.all([
    fetch('/templates/header.html').then(r => r.text()),
    fetch('/templates/footer.html').then(r => r.text()),
    fetch('/templates/head.html').then(r => r.text())
  ]);
  document.getElementById('site-header').innerHTML = header;
  document.getElementById('site-footer').innerHTML = footer;
  document.head.insertAdjacentHTML('afterbegin', head);

  const depth = window.location.pathname.split('/').filter(Boolean).length;
  const cssPath = depth >= 2 ? '../../assets/styles.css' : './assets/styles.css';
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = cssPath;
  document.head.appendChild(link);

  loadGtag();

  if (isHomepage) {
    const manifest = await fetch('/manifest.json').then(r => r.json());
    const latestPage = manifest.latest_page || 1;
    window.location.replace('/page/' + latestPage + '/');
    return;
  }

  await loadDayjs();
  enhanceDates();
}

function enhanceDates() {
  document.querySelectorAll('.post-date[data-date]').forEach(el => {
    el.textContent = dayjs(el.dataset.date).fromNow();
  });
}
