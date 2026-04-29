#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
from datetime import datetime

SITEMAP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sitemap.xml")
MAX_URLS_PER_SITEMAP = 50000


def init_sitemap():
    """Initialize new sitemap if it doesn't exist"""
    if not os.path.exists(SITEMAP_PATH):
        urlset = ET.Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        tree = ET.ElementTree(urlset)
        with open(SITEMAP_PATH, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)


def append_sitemap(url, lastmod=None, changefreq="weekly", priority="0.5"):
    """Append single URL to sitemap, avoid duplicates"""
    if lastmod is None:
        lastmod = datetime.now().strftime("%Y-%m-%d")

    init_sitemap()

    # Parse existing sitemap
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()

    # Check for existing URL
    for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if url_elem.text == url:
            return False

    # Don't exceed max limit
    if len(root) >= MAX_URLS_PER_SITEMAP:
        return False

    # Add new URL entry
    url_entry = ET.SubElement(root, "url")

    loc = ET.SubElement(url_entry, "loc")
    loc.text = url

    lm = ET.SubElement(url_entry, "lastmod")
    lm.text = lastmod

    cf = ET.SubElement(url_entry, "changefreq")
    cf.text = changefreq

    pr = ET.SubElement(url_entry, "priority")
    pr.text = priority

    # Write back file
    ET.indent(tree)
    with open(SITEMAP_PATH, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

    return True


def regenerate_full_sitemap(url_list):
    """Completely rebuild sitemap from list of URLs"""
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for item in url_list:
        url = item if isinstance(item, str) else item["url"]
        lastmod = item["lastmod"] if isinstance(item, dict) and "lastmod" in item else datetime.now().strftime("%Y-%m-%d")

        url_entry = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_entry, "loc")
        loc.text = url
        lm = ET.SubElement(url_entry, "lastmod")
        lm.text = lastmod
        cf = ET.SubElement(url_entry, "changefreq")
        cf.text = "weekly"
        pr = ET.SubElement(url_entry, "priority")
        pr.text = "0.5"

    tree = ET.ElementTree(urlset)
    ET.indent(tree)
    with open(SITEMAP_PATH, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

    return True
