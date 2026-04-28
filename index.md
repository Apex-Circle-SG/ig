---
layout: default
title: InsightGinie
---

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
