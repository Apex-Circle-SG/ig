---
layout: default
title: InsightGinie
---

# InsightGinie

Official site: <a href="https://insightginie.com">News of Tomorrow</a>

This repository is a mirror of the InsightGinie knowledge archive.

---

## Categories

{% assign mains = "" | split: "" %}

{% for post in site.posts %}
  {% if post.categories and post.categories.size > 0 %}
    {% assign main_cat = post.categories[0] %}
    {% if main_cat %}
      {% assign mains = mains | push: main_cat %}
    {% endif %}
  {% endif %}
{% endfor %}

{% assign mains = mains | uniq | sort %}

<ul>

{% for main in mains %}

<li>

<strong>{{ main | capitalize }}</strong>

<ul>

{% assign subs = "" | split: "" %}

{% for post in site.posts %}
  {% if post.categories and post.categories.size > 1 %}
    {% if post.categories[0] == main %}
      {% assign sub_cat = post.categories[1] %}
      {% if sub_cat %}
        {% assign subs = subs | push: sub_cat %}
      {% endif %}
    {% endif %}
  {% endif %}
{% endfor %}

{% assign subs = subs | uniq | sort %}

{% for sub in subs %}

<li>
<a href="/{{ main }}/{{ sub }}/">
{{ sub | capitalize }}
</a>
</li>

{% endfor %}

</ul>

</li>

{% endfor %}

</ul>