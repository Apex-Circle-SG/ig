let currentPage = 1;
let totalPages = 1;
let base = '';
const DEFAULT_IMAGE = 'https://picsum.photos/id/695/1200/630';
const SITE_NAME = 'InsightGinie Archive';
const SITE_DESC = 'News of Tomorrow';

const metaDesc = document.querySelector('meta[name="description"]');
const metaCanonical = document.querySelector('link[rel="canonical"]');
const ogTitle = document.querySelector('meta[property="og:title"]');
const ogDesc = document.querySelector('meta[property="og:description"]');
const ogImage = document.querySelector('meta[property="og:image"]');
const ogUrl = document.querySelector('meta[property="og:url"]');
const jsonLdSite = document.getElementById('jsonld-site');

document.addEventListener('DOMContentLoaded', init);

async function init() {
  base = window.location.pathname.split('/').slice(0, -1).join('/');
  const manifest = await fetch(base + '/manifest.json').then(r => r.json());
  totalPages = manifest.latest_page;
  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));
  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;

  const redirectedPath = params.get('route');
  if (redirectedPath) {
    history.replaceState(null, '', base + '/' + redirectedPath.replace(/^\/+/, ''));
  }

  const [header, footer] = await Promise.all([
    fetch(base + '/templates/header.html').then(r => r.text()),
    fetch(base + '/templates/footer.html').then(r => r.text())
  ]);
  document.getElementById('site-header').innerHTML = header;
  document.getElementById('site-footer').innerHTML = footer;

  window.addEventListener('popstate', handleRoute);
  handleRoute();
  document.getElementById('loading').style.display = 'none';
}

function normalizePath() {
  let path = window.location.pathname;
  if (path.startsWith(base)) path = path.slice(base.length);
  while (path.startsWith('/')) path = path.slice(1);
  while (path.endsWith('/')) path = path.slice(0, -1);
  return path;
}

function absoluteUrl(path = '') {
  return `${window.location.origin}${base}/${path}`.replace(/([^:]\/)\/+/g, '$1');
}

function setSeo({ title, description, image, url, jsonLd }) {
  document.title = title;
  metaDesc.setAttribute('content', description);
  metaCanonical.setAttribute('href', url);
  ogTitle.setAttribute('content', title);
  ogDesc.setAttribute('content', description);
  ogImage.setAttribute('content', image || DEFAULT_IMAGE);
  ogUrl.setAttribute('content', url);
  jsonLdSite.textContent = JSON.stringify(jsonLd);
}

async function handleRoute() {
  const path = normalizePath();
  if (!path || path === 'index.html') return renderPage(currentPage);
  return renderPost(path);
}

async function renderPage(pageNum) {
  currentPage = pageNum;
  const postsMap = await fetch(base + `/page/${pageNum}.json`).then(r => r.json());

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

  let html = '<ul class="post-list">';
  for (const [slug, post] of Object.entries(postsMap)) {
    html += `<li class="post-item"><a href="${base}/${slug}" onclick="navigate('${slug}'); return false;" class="post-title">${post.title}</a><span class="post-date">${post.date}</span><div>${post.excerpt || ''}</div></li>`;
  }
  html += '</ul>';
  document.getElementById('content').innerHTML = html;

  let phtml = '';
  if (currentPage > 1) phtml += `<button onclick="renderPage(${currentPage - 1})">&laquo; Previous</button>`;
  phtml += `<span>Page ${currentPage} / ${totalPages}</span>`;
  if (currentPage < totalPages) phtml += `<button onclick="renderPage(${currentPage + 1})">Next &raquo;</button>`;
  document.getElementById('pagination').innerHTML = phtml;
}

async function renderPost(slug) {
  slug = decodeURIComponent((slug || '').replace(/^\/+|\/+$/g, ''));
  const post = await fetch(base + `/data/${slug}.json`).then(r => r.json());

  setSeo({
    title: `${post.title} | ${SITE_NAME}`,
    description: post.excerpt || SITE_DESC,
    image: post.img || DEFAULT_IMAGE,
    url: absoluteUrl(slug),
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: post.title,
      datePublished: post.date,
      dateModified: post.date,
      image: [post.img || DEFAULT_IMAGE],
      description: post.excerpt || SITE_DESC,
      mainEntityOfPage: absoluteUrl(slug)
    }
  });

  document.getElementById('content').innerHTML = `
        <article>
            <h1>${post.title}</h1>
            <p style="color:#718096; font-size:0.9rem;">${post.date}</p>
            <img src="${post.img || DEFAULT_IMAGE}" style="width:100%; margin: 1rem 0; border-radius: 4px;" alt="${post.title}">
            ${post.content}
        </article>
    `;
  document.getElementById('pagination').innerHTML = `<button onclick="navigate(''); return false;">&laquo; Back to archive</button>`;
}

function navigate(slug) {
  const url = slug ? base + '/' + slug : base + '/';
  history.pushState(null, '', url);
  handleRoute();
}
