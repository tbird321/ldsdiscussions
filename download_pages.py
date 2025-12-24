#!/usr/bin/env python3
import json
import os
import re
from urllib.parse import urlparse
from datetime import datetime
import subprocess

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
            # Save the HTML content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            # Update the plan
            page['downloaded'] = True
            page['downloaded_at'] = datetime.now().isoformat()
            page['filename'] = filename
            
            downloaded_count += 1
            print(f"  ✓ Downloaded successfully")
        else:
            print(f"  ✗ Error downloading: {result.stderr}")
    
    # Write updated plan back
    with open('scraper-plan.json', 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"\nDownloaded {downloaded_count} pages")

if __name__ == '__main__':
    main()
