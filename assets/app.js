let currentPage = 1;
let totalPages = 1;
let base = '';
let pagePosts = [];
const POSTS_PER_PAGE = 100;
const DEFAULT_IMAGE = 'https://picsum.photos/id/695/1200/630';
const SITE_NAME = 'InsightGinie';
const SITE_DESC = 'News of Tomorrow';

const metaTitle = document.querySelector('meta[name="title"]');
const metaDesc = document.querySelector('meta[name="description"]');
const metaCanonical = document.querySelector('link[rel="canonical"]');

const ogTitle = document.querySelector('meta[property="og:title"]');
const ogDesc = document.querySelector('meta[property="og:description"]');
const ogImage = document.querySelector('meta[property="og:image"]');
const ogUrl = document.querySelector('meta[property="og:url"]');

const twTitle = document.querySelector('meta[property="twitter:title"]');
const twDesc = document.querySelector('meta[property="twitter:description"]');
const twImage = document.querySelector('meta[property="twitter:image"]');
const twUrl = document.querySelector('meta[property="twitter:url"]');

const jsonLdSite = document.getElementById('jsonld-site');

document.addEventListener('DOMContentLoaded', init);

async function init() {
  base = window.location.pathname.split('/').slice(0, -1).join('/');

  // Wait for dayjs to be available
  await waitForDayjs();

  try {
    const manifest = await fetch(base + '/manifest.json').then(r => r.json());
    totalPages = manifest.latest_page || 1;
  } catch(e) {
    console.error("Failed to load manifest", e);
    totalPages = 1;
  }

  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));
  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;

  try {
    const [header, footer] = await Promise.all([
      fetch(base + '/templates/header.html').then(r => r.text()),
      fetch(base + '/templates/footer.html').then(r => r.text())
    ]);
    document.getElementById('site-header').innerHTML = header;
    document.getElementById('site-footer').innerHTML = footer;

    // Evaluate script in footer
    const footerScripts = document.getElementById('site-footer').getElementsByTagName('script');
    for (let i = 0; i < footerScripts.length; i++) {
        eval(footerScripts[i].innerText);
    }
  } catch (e) {
      console.error("Failed to load templates", e);
  }

  window.addEventListener('popstate', handleRoute);
  await handleRoute();
  document.getElementById('loading').style.display = 'none';
}

function waitForDayjs() {
    return new Promise(resolve => {
        if (window.dayjs && window.dayjs_plugin_relativeTime) {
            dayjs.extend(window.dayjs_plugin_relativeTime);
            resolve();
            return;
        }
        const interval = setInterval(() => {
            if (window.dayjs && window.dayjs_plugin_relativeTime) {
                clearInterval(interval);
                dayjs.extend(window.dayjs_plugin_relativeTime);
                resolve();
            }
        }, 50);
    });
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
  if (metaTitle) metaTitle.setAttribute('content', title);
  if (metaDesc) metaDesc.setAttribute('content', description);
  if (metaCanonical) metaCanonical.setAttribute('href', url);

  if (ogTitle) ogTitle.setAttribute('content', title);
  if (ogDesc) ogDesc.setAttribute('content', description);
  if (ogImage) ogImage.setAttribute('content', image || DEFAULT_IMAGE);
  if (ogUrl) ogUrl.setAttribute('content', url);

  if (twTitle) twTitle.setAttribute('content', title);
  if (twDesc) twDesc.setAttribute('content', description);
  if (twImage) twImage.setAttribute('content', image || DEFAULT_IMAGE);
  if (twUrl) twUrl.setAttribute('content', url);

  if (jsonLdSite && jsonLd) jsonLdSite.textContent = JSON.stringify(jsonLd);
}

async function handleRoute() {
  const path = normalizePath();
  const params = new URLSearchParams(window.location.search);
  const urlPage = Number(params.get('page'));
  currentPage = Number.isFinite(urlPage) && urlPage >= 1 ? Math.min(urlPage, totalPages) : totalPages;

  document.getElementById('loading').style.display = 'flex';
  document.getElementById('content').innerHTML = '';
  document.getElementById('pagination').innerHTML = '';

  if (!path || path === 'index.html' || path === '') {
      await renderPage(currentPage);
  } else {
      await renderPost(path);
  }

  document.getElementById('loading').style.display = 'none';
  window.scrollTo(0, 0);
}

async function renderPage(pageNum) {
  currentPage = pageNum;
  try {
    pagePosts = await fetch(base + `/page/${pageNum}.json`).then(r => r.json());
  } catch (e) {
    console.error("Failed to fetch page data", e);
    pagePosts = [];
  }

  setSeo({
    title: SITE_NAME + ' - ' + SITE_DESC,
    description: "Discover the latest insights, news, and analysis on AI, Business, Finance, Tech, and more at InsightGinie.",
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

  if (pagePosts.length === 0) {
      document.getElementById('content').innerHTML = `
        <div class="text-center py-20">
            <h2 class="text-2xl font-bold text-gray-700">No articles found.</h2>
            <p class="text-gray-500 mt-2">Check back later for new content.</p>
        </div>
      `;
      return;
  }

  // Layout for the grid using Tailwind
  let html = `
    <div class="mb-10">
      <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight sm:text-4xl mb-4">Latest Articles</h1>
      <p class="text-lg text-gray-500">Stay updated with the newest trends and insights.</p>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
  `;

  for (const post of pagePosts) {
    const timeAgo = window.dayjs ? dayjs(post.date).fromNow() : post.date;
    const postImage = `https://picsum.photos/seed/${post.slug}/600/400`; // Dynamic image based on slug

    html += `
    <article class="flex flex-col bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow duration-300">
      <a href="${base}/${post.slug}" onclick="navigate('${post.slug}'); return false;" class="block overflow-hidden aspect-[3/2]">
        <img src="${postImage}" alt="Cover image for ${post.title}" class="w-full h-full object-cover transform hover:scale-105 transition-transform duration-500" loading="lazy">
      </a>
      <div class="flex flex-col flex-grow p-6">
        <div class="flex items-center text-sm text-gray-500 mb-3">
          <time datetime="${post.date}">${timeAgo}</time>
        </div>
        <a href="${base}/${post.slug}" onclick="navigate('${post.slug}'); return false;" class="block group">
          <h2 class="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2 mb-2">
            ${post.title}
          </h2>
          <p class="text-gray-600 line-clamp-3 text-sm">
            ${post.excerpt || 'Read the full article to learn more.'}
          </p>
        </a>
        <div class="mt-auto pt-4">
            <a href="${base}/${post.slug}" onclick="navigate('${post.slug}'); return false;" class="text-blue-600 font-medium text-sm hover:text-blue-800 flex items-center gap-1">
                Read article
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
            </a>
        </div>
      </div>
    </article>`;
  }
  html += '</div>';
  document.getElementById('content').innerHTML = html;

  let phtml = '';
  const btnClass = "inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors";
  const disabledClass = "inline-flex items-center px-4 py-2 border border-gray-200 text-sm font-medium rounded-md text-gray-400 bg-gray-50 cursor-not-allowed";

  // Reverse logic: Page 1 is the oldest, totalPages is the newest.
  if (currentPage < totalPages) {
      phtml += `<button onclick="renderPage(${currentPage + 1})" class="${btnClass}">&larr; Newer</button>`;
  } else {
      phtml += `<span class="${disabledClass}">&larr; Newer</span>`;
  }

  phtml += `<span class="text-sm font-medium text-gray-700">Page ${totalPages - currentPage + 1} of ${totalPages}</span>`;

  if (currentPage > 1) {
      phtml += `<button onclick="renderPage(${currentPage - 1})" class="${btnClass}">Older &rarr;</button>`;
  } else {
      phtml += `<span class="${disabledClass}">Older &rarr;</span>`;
  }

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
    try {
        const response = await fetch(base + `/data/${candidate}.json`);
        if (response.ok) {
            const post = await response.json();
            return { post, resolvedSlug: candidate };
        }
    } catch (e) {
        // ignore network error for candidate, try next
    }
  }
  throw new Error(`Post not found for slug: ${slug}`);
}

async function renderPost(slug) {
  try {
      const { post, resolvedSlug } = await fetchPostBySlug(slug);

      const postImage = post.img || `https://picsum.photos/seed/${post.slug || slug}/1200/630`;

      setSeo({
        title: `${post.title} - ${SITE_NAME}`,
        description: post.excerpt || SITE_DESC,
        image: postImage,
        url: absoluteUrl(resolvedSlug),
        jsonLd: {
          '@context': 'https://schema.org',
          '@type': 'Article',
          headline: post.title,
          datePublished: post.date,
          dateModified: post.date,
          image: [postImage],
          description: post.excerpt || SITE_DESC,
          mainEntityOfPage: absoluteUrl(resolvedSlug),
          author: {
             "@type": "Organization",
             "name": SITE_NAME
          }
        }
      });

      const formattedDate = window.dayjs ? dayjs(post.date).format('MMMM D, YYYY') : post.date;

      document.getElementById('content').innerHTML = `
            <article class="max-w-3xl mx-auto bg-white sm:rounded-2xl sm:shadow-sm sm:border border-gray-100 overflow-hidden">
                <header class="px-4 pt-10 pb-6 sm:px-8 sm:pt-12 sm:pb-8 border-b border-gray-100">
                    <h1 class="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight mb-4 leading-tight">${post.title}</h1>
                    <div class="flex items-center text-gray-500 text-sm">
                        <time datetime="${post.date}" class="flex items-center">
                            <svg class="mr-1.5 h-4 w-4 flex-shrink-0 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path fill-rule="evenodd" d="M5.75 2a.75.75 0 01.75.75V4h7V2.75a.75.75 0 011.5 0V4h.25A2.75 2.75 0 0118 6.75v8.5A2.75 2.75 0 0115.25 18H4.75A2.75 2.75 0 012 15.25v-8.5A2.75 2.75 0 014.75 4H5V2.75A.75.75 0 015.75 2zM4.75 5.5a1.25 1.25 0 00-1.25 1.25v.75h13v-.75a1.25 1.25 0 00-1.25-1.25H4.75z" clip-rule="evenodd" />
                            </svg>
                            ${formattedDate}
                        </time>
                    </div>
                </header>

                <figure class="w-full">
                    <img src="${postImage}" alt="Cover image for ${post.title}" class="w-full h-auto max-h-[500px] object-cover" loading="eager">
                </figure>

                <div class="px-4 py-8 sm:px-8 sm:py-10 text-gray-800">
                    ${post.content}
                </div>
            </article>
        `;

      document.getElementById('pagination').innerHTML = `
        <div class="max-w-3xl mx-auto w-full px-4 sm:px-0">
            <button onclick="navigate(''); return false;" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to all articles
            </button>
        </div>`;
  } catch (err) {
      console.error(err);
      document.getElementById('content').innerHTML = `
        <div class="max-w-2xl mx-auto text-center py-20">
            <h1 class="text-4xl font-extrabold text-gray-900 mb-4">404</h1>
            <h2 class="text-2xl font-bold text-gray-700 mb-6">Article not found</h2>
            <p class="text-gray-500 mb-8">The article you're looking for doesn't exist or has been moved.</p>
            <button onclick="navigate(''); return false;" class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 transition-colors">
                Return to home
            </button>
        </div>
      `;
  }
}

function navigate(slug) {
  const url = slug ? base + '/' + slug : base + '/';
  history.pushState(null, '', url);
  handleRoute();
}
