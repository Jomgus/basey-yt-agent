import os
import psycopg2
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyBoStG3HWUr31_X1dMpJ7oU6cyo0eY_rzg")
DATABASE_URL = os.getenv("DATABASE_URL")

def scout_competitors(query="Texas life insurance tips"):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    # 1. Search for top 10 winning videos in the niche
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=10,
        order="viewCount", # Find the 'winners'
        publishedAfter="2025-01-01T00:00:00Z" # Stay modern
    )
    response = request.execute()

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # 2. Store them as 'Targets' for the agent
    for item in response.get('items', []):
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        
        cur.execute("""
            INSERT INTO youtube_benchmarks (video_id, title)
            VALUES (%s, %s) ON CONFLICT (video_id) DO NOTHING;
        """, (video_id, title))
    
    conn.commit()
    print(f"Scout complete. Found {len(response['items'])} competitor targets.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    scout_competitors()