#!/usr/bin/env python3
import json
import re
from urllib.parse import urljoin, urlparse, urlunparse
from html.parser import HTMLParser

class LinkExtractor(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = set()
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href' and value:
                    # Normalize the URL
                    full_url = urljoin(self.base_url, value)
                    parsed = urlparse(full_url)
                    
                    # Skip if not same domain
                    if parsed.netloc and 'ldsdiscussions.com' not in parsed.netloc:
                        continue
                    
                    # Skip fragments, mailto, javascript, etc.
                    if parsed.scheme and parsed.scheme not in ['http', 'https', '']:
                        continue
                    
                    # Remove fragment
                    clean_url = urlunparse((
                        parsed.scheme or 'https',
                        parsed.netloc or 'www.ldsdiscussions.com',
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        ''  # Remove fragment
                    ))
                    
                    # Only add if it's a page on ldsdiscussions.com
                    if 'ldsdiscussions.com' in clean_url:
                        self.links.add(clean_url)

def main():
    base_url = 'https://www.ldsdiscussions.com/'
    
    # Read the HTML file
    with open('/tmp/homepage.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse HTML and extract links
    parser = LinkExtractor(base_url)
    parser.feed(html_content)
    
    # Convert to sorted list
    links = sorted(list(parser.links))
    
    # Read existing plan
    with open('scraper-plan.json', 'r') as f:
        plan = json.load(f)
    
    # Add all unique links to pages array
    existing_urls = {page['url'] for page in plan['pages']}
    for link in links:
        if link not in existing_urls:
            plan['pages'].append({
                'url': link,
                'downloaded': False
            })
    
    # Write back to plan file
    with open('scraper-plan.json', 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"Found {len(links)} unique links")
    print(f"Total pages in plan: {len(plan['pages'])}")

if __name__ == '__main__':
    main()
