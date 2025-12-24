#!/usr/bin/env python3
import json
import os
import re
from urllib.parse import urlparse
from datetime import datetime
import subprocess
from html.parser import HTMLParser

def sanitize_filename(url):
    """Create a safe filename from a URL"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    if not path:
        return 'index.html'
    
    # Replace slashes and special characters
    filename = re.sub(r'[^\w\-_\.]', '_', path)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Add .html extension if not present
    if not filename.endswith('.html'):
        filename += '.html'
    
    return filename

class ContentChecker(HTMLParser):
    """Extract text content from HTML to check if page has meaningful content"""
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.in_script = False
        self.in_style = False
    
    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True
    
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
    
    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            # Clean up whitespace and add non-empty text
            text = data.strip()
            if text:
                self.text_content.append(text)
    
    def get_text_length(self):
        """Get total length of extracted text content"""
        return len(' '.join(self.text_content))
    
    def has_meaningful_content(self, min_length=200):
        """Check if page has substantial content"""
        text_length = self.get_text_length()
        
        # Check for error indicators
        text_lower = ' '.join(self.text_content).lower()
        error_indicators = ['404', '500', 'error', 'not found', 'page not found']
        if any(indicator in text_lower for indicator in error_indicators):
            if text_length < 500:  # Error pages are usually short
                return False
        
        # Check if we have enough text content
        return text_length >= min_length

def main():
    # Create content folder if it doesn't exist
    content_dir = 'content'
    os.makedirs(content_dir, exist_ok=True)
    
    # Read the plan file
    with open('scraper-plan.json', 'r') as f:
        plan = json.load(f)
    
    # Find pages that haven't been downloaded
    pages_to_download = [page for page in plan['pages'] if not page.get('downloaded', False)]
    
    # Download up to 5 pages
    downloaded_count = 0
    for page in pages_to_download[:5]:
        url = page['url']
        filename = sanitize_filename(url)
        filepath = os.path.join(content_dir, filename)
        
        print(f"Downloading {url} -> {filepath}")
        
        # Download using curl
        result = subprocess.run(
            ['curl', '-s', '-L', url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            html_content = result.stdout
            
            # Check if page has meaningful content
            parser = ContentChecker()
            parser.feed(html_content)
            
            skip_reason = None
            if not parser.has_meaningful_content():
                text_length = parser.get_text_length()
                if text_length < 200:
                    skip_reason = "skipped - blank page"
                else:
                    skip_reason = "skipped - no content"
                print(f"  ⚠ {skip_reason} (text length: {text_length})")
            else:
                # Save the HTML content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                downloaded_count += 1
                print(f"  ✓ Downloaded successfully")
            
            # Always mark as downloaded, regardless of whether we saved it
            page['downloaded'] = True
            page['downloaded_at'] = datetime.now().isoformat()
            if skip_reason:
                page['skip_reason'] = skip_reason
            else:
                page['filename'] = filename
        else:
            print(f"  ✗ Error downloading: {result.stderr}")
            # Still mark as downloaded to avoid retrying failed downloads
            page['downloaded'] = True
            page['downloaded_at'] = datetime.now().isoformat()
            page['skip_reason'] = f"error - {result.stderr[:50]}"
    
    # Write updated plan back
    with open('scraper-plan.json', 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"\nDownloaded {downloaded_count} pages")

if __name__ == '__main__':
    main()
