import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def get_video_details(video_id: str):
    logger.debug(f"Getting video details for {video_id}")
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    if response["items"]:
        item = response["items"][0]
        return {
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
        }
    return None


def get_video_transcript(video_id: str):
    logger.debug(f"Getting video transcript for {video_id}")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None


def get_video_comments(video_id: str, max_results: int = 100):
    logger.debug(f"Getting video comments for {video_id}")
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        order="relevance",  # This sorts comments by relevance
    )
    response = request.execute()
    return [
        item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        for item in response["items"]
    ]
