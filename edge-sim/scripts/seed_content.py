"""
Seed Content Script
Creates sample content in the database for testing
"""
import asyncio
import httpx
import json
from typing import List, Dict

BACKEND_URL = "http://localhost:8000"

# Sample content to create
SAMPLE_CONTENT = [
    {"content_id": "video-001", "content_type": "video", "size_kb": 5000, "category": "entertainment"},
    {"content_id": "video-002", "content_type": "video", "size_kb": 3000, "category": "entertainment"},
    {"content_id": "video-003", "content_type": "video", "size_kb": 8000, "category": "sports"},
    {"content_id": "image-001", "content_type": "image", "size_kb": 200, "category": "news"},
    {"content_id": "image-002", "content_type": "image", "size_kb": 150, "category": "news"},
    {"content_id": "image-003", "content_type": "image", "size_kb": 300, "category": "entertainment"},
    {"content_id": "html-001", "content_type": "html", "size_kb": 50, "category": "news"},
    {"content_id": "html-002", "content_type": "html", "size_kb": 75, "category": "sports"},
    {"content_id": "html-003", "content_type": "html", "size_kb": 100, "category": "entertainment"},
]


async def create_content(content: Dict, client: httpx.AsyncClient) -> bool:
    """Create a single content item"""
    try:
        # Note: This endpoint will be created in Part 5
        # For now, we'll insert directly into database or use a placeholder
        response = await client.post(
            f"{BACKEND_URL}/api/v1/content",
            json=content,
            timeout=5.0
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ Created {content['content_id']}")
            return True
        else:
            print(f"✗ Failed to create {content['content_id']}: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error creating {content['content_id']}: {e}")
        return False


async def seed_content():
    """Seed sample content into database"""
    print("Seeding content into database...")
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    client = httpx.AsyncClient()
    
    success_count = 0
    
    try:
        for content in SAMPLE_CONTENT:
            # Add sample data
            content_data = {
                **content,
                "data": {
                    "title": f"Sample {content['content_type']} content",
                    "description": f"This is sample {content['content_type']} content",
                    "url": f"https://example.com/{content['content_id']}"
                }
            }
            
            if await create_content(content_data, client):
                success_count += 1
        
        print()
        print(f"Successfully created {success_count}/{len(SAMPLE_CONTENT)} content items")
        
    finally:
        await client.aclose()


if __name__ == "__main__":
    print("=" * 50)
    print("Content Seeding Script")
    print("=" * 50)
    print()
    print("Note: This script requires the backend content API to be implemented.")
    print("For now, you can manually insert content using SQL:")
    print()
    print("INSERT INTO content (content_id, content_type, size_kb, category) VALUES")
    print("  ('video-001', 'video', 5000, 'entertainment'),")
    print("  ('image-001', 'image', 200, 'news'),")
    print("  ...")
    print()
    print("=" * 50)
    print()
    
    # Uncomment to run (when backend API is ready):
    # asyncio.run(seed_content())
