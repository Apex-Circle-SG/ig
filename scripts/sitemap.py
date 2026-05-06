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
    """DEPRECATED: Use batch_append_sitemap for better performance with multiple URLs.
    
    Append single URL to sitemap, avoid duplicates. This function parses the entire 
    sitemap XML tree for each call, making it O(n²) for n URLs. Use batch_append_sitemap
    instead for O(n) performance.
    """
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


def batch_append_sitemap(url_entries):
    """
    Efficiently append multiple URLs to the sitemap in a single operation.
    
    This function uses string manipulation instead of XML parsing, making it
    O(n) for n URLs instead of O(n²) with the old append_sitemap approach.
    
    Args:
        url_entries: List of dicts with keys: url (required), lastmod (optional),
                     changefreq (optional, default 'weekly'), 
                     priority (optional, default '0.5')
    
    Returns:
        int: Number of URLs successfully appended
    """
    if not url_entries:
        return 0
    
    init_sitemap()
    
    # Read the entire sitemap as a string
    with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and remove the closing </urlset> tag
    urlset_close_pos = content.rfind('</urlset>')
    if urlset_close_pos == -1:
        # Malformed XML, fallback to ElementTree method
        count = 0
        for entry in url_entries:
            if append_sitemap(
                entry['url'],
                entry.get('lastmod'),
                entry.get('changefreq', 'weekly'),
                entry.get('priority', '0.5')
            ):
                count += 1
        return count
    
    # Build new URL entries as raw XML strings
    new_entries_xml = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for entry in url_entries:
        url = entry['url']
        lastmod = entry.get('lastmod', today)
        changefreq = entry.get('changefreq', 'weekly')
        priority = entry.get('priority', '0.5')
        
        xml_entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
"""
        new_entries_xml.append(xml_entry)
    
    # Reconstruct the sitemap with new entries inserted before </urlset>
    new_content = content[:urlset_close_pos] + ''.join(new_entries_xml) + '  </urlset>\n'
    
    # Write back
    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return len(url_entries)


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
