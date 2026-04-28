---
layout: default
pagination: 
  enabled: true
---

<h1>All Articles</h1>

<ul>
{% for post in paginator.posts %}
  <li>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    <br>
    <small>{{ post.date | date: "%B %d, %Y" }}</small>
  </li>
{% endfor %}
</ul>

{% if paginator.total_pages > 1 %}
<div class="pagination">
  {% if paginator.previous_page %}
    <a href="{{ paginator.previous_page_path | relative_url }}">&laquo; Previous</a>
  {% endif %}

  <span>Page {{ paginator.page }} of {{ paginator.total_pages }}</span>

  {% if paginator.next_page %}
    <a href="{{ paginator.next_page_path | relative_url }}">Next &raquo;</a>
  {% endif %}
</div>
{% endif %}


# InsightGinie

Official site: <a href="https://insightginie.com">News of Tomorrow</a>

This repository is a mirror of the InsightGinie knowledge archive.

---

## Categories

<ul>

{% for main in site.data.categories %}

<li>

<strong>{{ main.name }}</strong>

<ul>

{% for sub in main.subcategories %}

<li>
<a href="/{{ main.slug }}/{{ sub.slug }}/">
{{ sub.name }}
</a>
</li>

{% endfor %}

</ul>

</li>

{% endfor %}

</ul>
