let currentPage = 1;
let totalPages = 1;
let pagePosts = [];
const POSTS_PER_PAGE = 100;
const DEFAULT_IMAGE = 'https://picsum.photos/id/695/1200/630';
const SITE_NAME = 'InsightGinie Archive';
const SITE_DESC = 'News of Tomorrow';

const isPostPage = !!document.querySelector('article') && !document.getElementById('content');

document.addEventListener('DOMContentLoaded', init);

async function init() {
  const [header, footer] = await Promise.all([
    fetch('/templates/header.html').then(r => r.text()),
    fetch('/templates/footer.html').then(r => r.text())
  ]);
  document.getElementById('site-header').innerHTML = header;
  document.getElementById('site-footer').innerHTML = footer;

  if (isPostPage) return;

  const manifest = await fetch('/manifest.json').then(r => r.json());
  totalPages = manifest.latest_page || 1;

  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));
  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;

  window.addEventListener('popstate', handleRoute);
  handleRoute();
  document.getElementById('loading').style.display = 'none';
}

function absoluteUrl(path = '') {
  return `https://github.insightginie.com/${path}`.replace(/([^:]\/)\/+/g, '$1');
}

function setSeo({ title, description, image, url, jsonLd }) {
  document.title = title;
  const metaDesc = document.querySelector('meta[name="description"]');
  const metaCanonical = document.querySelector('link[rel="canonical"]');
  const ogTitle = document.querySelector('meta[property="og:title"]');
  const ogDesc = document.querySelector('meta[property="og:description"]');
  const ogImage = document.querySelector('meta[property="og:image"]');
  const ogUrl = document.querySelector('meta[property="og:url"]');
  const jsonLdSite = document.getElementById('jsonld-site');
  metaDesc.setAttribute('content', description);
  metaCanonical.setAttribute('href', url);
  ogTitle.setAttribute('content', title);
  ogDesc.setAttribute('content', description);
  ogImage.setAttribute('content', image || DEFAULT_IMAGE);
  ogUrl.setAttribute('content', url);
  jsonLdSite.textContent = JSON.stringify(jsonLd);
}

async function handleRoute() {
  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));
  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;
  renderPage(currentPage);
}

async function renderPage(pageNum) {
  currentPage = pageNum;
  try {
    pagePosts = await fetch(`/page/${pageNum}.json`).then(r => r.json());
  } catch (e) {
    pagePosts = [];
  }

  setSeo({
    title: SITE_NAME,
    description: SITE_DESC,
    image: DEFAULT_IMAGE,
    url: absoluteUrl(pageNum === totalPages ? '' : `?page=${pageNum}`),
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': 'CollectionPage',
      name: SITE_NAME,
      description: SITE_DESC,
      url: absoluteUrl(pageNum === totalPages ? '' : `?page=${pageNum}`)
    }
  });

  let html = '<div class="post-list">';
  for (const post of pagePosts) {
    const timeAgo = dayjs(post.date).fromNow();
    let displayExcerpt = post.excerpt || '';
    if (displayExcerpt.length > 3) {
      displayExcerpt = displayExcerpt.slice(0, -3) + '...';
    } else if (displayExcerpt.length > 0) {
      displayExcerpt = displayExcerpt + '...';
    }
    html += `<div class="post-item">
      <a href="/posts/${post.slug}/">
        <img src="https://picsum.photos/seed/${post.slug}/100/50" class="post-thumb" alt="${post.title}" loading="lazy">
      </a>
      <a href="/posts/${post.slug}/" class="post-title">${post.title}</a>
      <span class="post-date">${timeAgo}</span>
      <div class="post-excerpt">${displayExcerpt}</div>
    </div>`;
  }
  html += '</div>';
  document.getElementById('content').innerHTML = html;

  let phtml = '';
  if (currentPage < totalPages) phtml += `<a href="?page=${currentPage + 1}" class="button">&laquo; Newer Posts</a>`;
  phtml += `<span>Page ${currentPage} / ${totalPages}</span>`;
  if (currentPage > 1) phtml += `<a href="?page=${currentPage - 1}" class="button">Older Posts &raquo;</a>`;
  document.getElementById('pagination').innerHTML = phtml;
}
