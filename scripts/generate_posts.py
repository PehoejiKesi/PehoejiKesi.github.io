import os
import re
import hashlib
import asyncio
from datetime import datetime, timedelta
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
                    match = re.search(r'\[.*?\]\((.*?)\)|(https?://\S+)', subline[5:].strip())
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

def generate_post_content(item, modal_id, img_filename, date_str):
    # We need a filename that Jekyll picks up. 
    # Date comes from the main loop
    
    content = f"""---
layout: default
modal-id: {modal_id}
date: {date_str}
img: generated/{img_filename}
alt: {item['title']}
category: {item['category']}
description: {item['description']}
link: {item['link']}
title: {item['title']}
---
"""
    return content

async def main():
    items = parse_readme()
    
    # Clean up old posts (both old 'generated-' and new date-based ones if reasonable)
    # For safety, let's just clean specific known patterns or specific files we track.
    # But since we are changing the pattern, we'll try to clean what we know.
    if os.path.exists(POSTS_DIR):
        import shutil
        shutil.rmtree(POSTS_DIR)
        os.makedirs(POSTS_DIR)

    if os.path.exists(IMG_DIR):
        import shutil
        shutil.rmtree(IMG_DIR)
    os.makedirs(IMG_DIR, exist_ok=True)
    
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    
    start_date = datetime(2000, 1, 1)
    
    # User requested same date for all: 2000-01-01
    date_str = start_date.strftime("%Y-%m-%d")

    for idx, item in enumerate(items, start=1):
        # User requested content modal-id to be 1, 2, 3... (just the integer)
        modal_id = idx
        
        # Filename pattern needs to be unique and ordered: 2000-01-01-{idx}
        filename_id = f"{date_str}-{idx}"
        
        img_filename = f"{modal_id}.png"
        img_path = os.path.join(IMG_DIR, img_filename)
        
        # Always generate screenshot (overwrite if exists)
        await capture_screenshot(item['link'], img_path)
        
        # Pass simple modal_id (int or str)
        post_content = generate_post_content(item, modal_id, img_filename, date_str)
        
        # Filename pattern: YYYY-MM-DD-{idx}.markdown
        post_filename = f"{filename_id}.markdown"
        with open(os.path.join(POSTS_DIR, post_filename), "w", encoding="utf-8") as f:
            f.write(post_content)
        
        print(f"Generated post: {post_filename}")

if __name__ == "__main__":
    asyncio.run(main())
