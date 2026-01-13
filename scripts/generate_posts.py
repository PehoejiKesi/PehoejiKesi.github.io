import os
import re
import hashlib
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image

README_PATH = "README.md"
POSTS_DIR = "_posts"
IMG_DIR = "img/portfolio/generated"

def parse_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse categories and items
    # Structure:
    # ## Category
    # ### Title
    # link: ...
    # description: ...
    
    items = []
    current_category = None
    
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('## '):
            current_category = line[3:].strip()
        elif line.startswith('### '):
            if not current_category:
                i += 1
                continue
                
            title = line[4:].strip()
            link = None
            description = None
            
            # Look ahead for attributes
            j = i + 1
            while j < len(lines):
                subline = lines[j].strip()
                if subline.startswith('##'): # Next section
                    break
                
                if subline.startswith('link:'):
                    # Extract link URL from markdown link [desc](url) or plain url
                    match = re.search(r'\((.*?)\)|(https?://\S+)', subline[5:].strip())
                    if match:
                        link = match.group(1) or match.group(2)
                elif subline.startswith('description:'):
                    description = subline[12:].strip()
                
                j += 1
            
            if title and link:
                items.append({
                    'category': current_category,
                    'title': title,
                    'link': link,
                    'description': description or ""
                })
        i += 1
        
    return items

async def capture_screenshot(url, output_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 720})
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle')
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            await page.screenshot(path=output_path)
            
            # Resize image
            with Image.open(output_path) as img:
                img.thumbnail((800, 800))
                img.save(output_path)
                
            print(f"Captured screenshot for {url}")
        except Exception as e:
            print(f"Failed to capture screenshot for {url}: {e}")
            # Create a placeholder or copy a default image if needed
        finally:
            await browser.close()

def generate_post_content(item, modal_id, img_filename):
    # Using a fixed date or current date? 
    # For reproducible builds, we might want a fixed date or based on README mod time.
    # But for simplicity, let's use a dummy date for now, or just keep the sample's date style.
    # The sample uses 9999-09-29, effectively pinning it. 
    # Let's use 2024-01-01 plus modal_id as a differentiator if we needed date sorting,
    # but modal-id suggests we just need unique files.
    
    # We need a filename that Jekyll picks up. 
    date_str = "2024-01-01" 
    
    content = f"""---
layout: default
modal-id: {modal_id}
date: {date_str}
img: generated/{img_filename}
alt: {item['title']}
project-date: April 2014
client: Start Bootstrap
category: {item['category']}
description: {item['description']}
link: {item['link']}
title: {item['title']}
---
"""
    return content

async def main():
    items = parse_readme()
    
    # Clean up old posts
    if os.path.exists(POSTS_DIR):
        for f in os.listdir(POSTS_DIR):
            if f.startswith("generated-"):
                os.remove(os.path.join(POSTS_DIR, f))
    
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    
    for idx, item in enumerate(items):
        # Generate a stable ID based on title using hashlib (std hash is not stable)
        # using integer modulo 1000000 for a shorter but likely unique ID
        title_hash = hashlib.md5(item['title'].encode('utf-8')).hexdigest()
        modal_id = int(title_hash, 16) % 1000000
        
        title_slug = re.sub(r'[^a-zA-Z0-9]', '-', item['title']).lower()
        
        img_filename = f"{title_slug}.png"
        img_path = os.path.join(IMG_DIR, img_filename)
        
        # Always generate screenshot (overwrite if exists)
        await capture_screenshot(item['link'], img_path)
            
        post_content = generate_post_content(item, modal_id, img_filename)
        
        post_filename = f"generated-{idx}-{title_slug}.markdown"
        with open(os.path.join(POSTS_DIR, post_filename), "w", encoding="utf-8") as f:
            f.write(post_content)
        
        print(f"Generated post: {post_filename}")

if __name__ == "__main__":
    asyncio.run(main())
