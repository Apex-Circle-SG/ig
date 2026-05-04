let currentPage = 1;
let totalPages = 1;
let base = '';
let pagePosts = [];
const POSTS_PER_PAGE = 100;
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
  totalPages = manifest.latest_page || 1;

  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));
  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;

  const routeParam = params.get('route');
  if (routeParam) {
    history.replaceState(null, '', base + '/' + routeParam);
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
  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));

  if (path.startsWith('page/')) {
    const pageMatch = path.match(/^page\/(\d+)$/);
    if (pageMatch) {
      currentPage = Number(pageMatch[1]);
      currentPage = Number.isFinite(currentPage) && currentPage >= 1 ? Math.min(currentPage, totalPages) : totalPages;
      return renderPage(currentPage);
    }
  }

  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;

  if (!path || path === 'index.html') return renderPage(currentPage);
  return renderPost(path);
}

async function renderPage(pageNum) {
  currentPage = pageNum;
  try {
    pagePosts = await fetch(base + `/page/${pageNum}.json`).then(r => r.json());
  } catch (e) {
    pagePosts = [];
  }

  setSeo({
    title: SITE_NAME,
    description: SITE_DESC,
    image: DEFAULT_IMAGE,
    url: absoluteUrl(pageNum === totalPages ? '' : `page/${pageNum}`),
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': 'CollectionPage',
      name: SITE_NAME,
      description: SITE_DESC,
      url: absoluteUrl(pageNum === totalPages ? '' : `page/${pageNum}`)
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
      <a href="${base}/${post.slug}">
        <img src="https://picsum.photos/seed/${post.slug}/100/50" class="post-thumb" alt="${post.title}" loading="lazy">
      </a>
      <a href="${base}/${post.slug}" class="post-title">${post.title}</a>
      <span class="post-date">${timeAgo}</span>
      <div class="post-excerpt">${displayExcerpt}</div>
    </div>`;
  }
  html += '</div>';
  document.getElementById('content').innerHTML = html;

  let phtml = '';
  // Since chunk N is the newest, "Previous" means going to older posts (N-1)
  // But standard UI usually has "Older" or "Next Page" pointing to N-1
  if (currentPage < totalPages) phtml += `<a href="${base}/page/${currentPage + 1}" class="button">&laquo; Newer Posts</a>`;
  phtml += `<span>Page ${currentPage} / ${totalPages}</span>`;
  if (currentPage > 1) phtml += `<a href="${base}/page/${currentPage - 1}" class="button">Older Posts &raquo;</a>`;
  document.getElementById('pagination').innerHTML = phtml;
}

async function fetchPostBySlug(slug) {
  const clean = (slug || '').replace(/^\/+|\/+$/g, '');
  const candidates = Array.from(new Set([
    clean,
    encodeURI(clean),
    (() => {
      try {
        return encodeURI(decodeURIComponent(clean));
      } catch (_) {
        return clean;
      }
    })()
  ]));

  for (const candidate of candidates) {
    const response = await fetch(base + `/data/${candidate}.json`);
    if (response.ok) {
      const post = await response.json();
      return { post, resolvedSlug: candidate };
    }
  }
  throw new Error(`Post not found for slug: ${slug}`);
}

async function renderPost(slug) {
  const { post, resolvedSlug } = await fetchPostBySlug(slug);

  const postImageUrl = `https://picsum.photos/seed/${resolvedSlug}/800/400`;

  setSeo({
    title: `${post.title} | ${SITE_NAME}`,
    description: post.excerpt || SITE_DESC,
    image: postImageUrl,
    url: absoluteUrl(resolvedSlug),
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: post.title,
      datePublished: post.date,
      dateModified: post.date,
      image: [postImageUrl],
      description: post.excerpt || SITE_DESC,
      mainEntityOfPage: absoluteUrl(resolvedSlug)
    }
  });

  document.getElementById('content').innerHTML = `
        <article>
            <h1>${post.title}</h1>
            <p style="color:#718096; font-size:0.9rem;">${post.date}</p>
            <img src="${postImageUrl}" style="width:100%; margin: 1rem 0; border-radius: 4px;" alt="${post.title}">
            ${post.content}
        </article>
    `;
  document.getElementById('pagination').innerHTML = `<a href="${base}/" class="button">&laquo; Back to archive</a>`;
}
