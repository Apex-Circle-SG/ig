# InsightGinie Archive

Public static mirror/archive of https://insightginie.com hosted on GitHub Pages.

This repository contains the complete static archive of all InsightGinie articles, automatically synced from the live WordPress site.

## About

This is a read-only public mirror of the InsightGinie knowledge base. All content is automatically imported and kept in sync.

- **Live mirror**: https://github.insightginie.com
- **Original site**: https://insightginie.com
- **Generator**: Jekyll
- **Hosting**: GitHub Pages

## Repository Structure

```
├── _config.yml              Jekyll configuration
├── _data/categories.yml     Category definitions
├── _layouts/                Page templates
├── scripts/                 Sync utilities
│   └── sync_wordpress.py    WordPress content importer
├── ai/                      AI & Machine Learning articles
├── business/                Business & Strategy articles
├── eclectic/                Science, Philosophy, Mathematics
├── finance/                 Finance & Banking articles
├── game/                    Gaming & Metaverse
├── health/                  Health & Medical Technology
├── sales/                   Sales & Psychology
├── tech/                    Technology & Engineering
├── trading/                 Trading & Markets analysis
├── web3/                    Web3 & Cryptocurrency
└── uncategorized/
```

## How it works

1.  Content is pulled automatically from the live WordPress site using the official REST API
2.  Posts are converted to markdown format with proper Jekyll frontmatter
3.  Articles are sorted into the correct category directories
4.  Incremental sync maintains only new posts since last import
5.  GitHub Actions automatically builds and deploys the static site on every commit

## Syncing Content

To run a full content sync:
```bash
cd scripts
python sync_wordpress.py
```

This will:
- Fetch all published articles from insightginie.com
- Import any new posts not already in the archive
- Update sync state
- Place files into correct category folders

## License

Content copyright respective authors.
## Project Memory (Important)

- `manifest.json` must remain minimal and only contain:
  - `latest_page`
  - `last_synced_post_id`
- Archive listing metadata (`slug`, `title`, `date`, `excerpt`) must be sourced from `posts.json`.
- Frontend (`assets/app.js`) should paginate `posts.json` at 100 posts per page and use `manifest.json` only for sync/page bounds.
- Keep this contract stable across future refactors to avoid reworking pagination/sync behavior in new containers.
