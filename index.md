---
layout: default
---

<style>
  .archive-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
  }
  .post-list {
    max-width: 800px;
    margin: 0 auto;
    list-style: none;
    padding: 0;
  }
  .post-item {
    padding: 0.75rem 0;
    border-bottom: 1px solid #f5f5f5;
  }
  .post-title {
    font-size: 1.1rem;
    font-weight: 500;
    text-decoration: none;
    color: #2d3748;
  }
  .post-title:hover {
    color: #2b6cb0;
  }
  .post-date {
    font-size: 0.85rem;
    color: #718096;
    margin-top: 0.25rem;
    display: block;
  }
  .pagination {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
    padding: 1rem;
    align-items: center;
  }
  .pagination a {
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    background: #edf2f7;
    color: #2d3748;
  }
  .pagination a:hover {
    background: #e2e8f0;
  }
  .pagination span {
    color: #718096;
  }
  .site-footer {
    max-width: 800px;
    margin: 3rem auto 2rem auto;
    padding-top: 2rem;
    border-top: 1px solid #eee;
    text-align: center;
    color: #718096;
    font-size: 0.9rem;
  }
</style>

<div class="archive-header">
  <h1>InsightGinie Archive</h1>
  <p>News of Tomorrow</p>
</div>

<ul class="post-list">
{% for post in site.posts %}
  <li class="post-item">
    <a href="{{ post.url | relative_url }}" class="post-title">{{ post.title }}</a>
    <span class="post-date">{{ post.date | date: "%B %d, %Y" }}</span>
  </li>
{% endfor %}
</ul>

{% if paginator.total_pages > 1 %}
<div class="pagination">
  {% if paginator.previous_page %}
    <a href="{{ paginator.previous_page_path | relative_url }}">&laquo; Previous</a>
  {% endif %}

  <span>Page {{ paginator.page }} / {{ paginator.total_pages }}</span>

  {% if paginator.next_page %}
    <a href="{{ paginator.next_page_path | relative_url }}">Next &raquo;</a>
  {% endif %}
</div>
{% endif %}

<div class="site-footer">
  <p>Official site: <a href="https://insightginie.com">insightginie.com</a></p>
  <p>This is a public mirror archive.</p>
</div>

