import os
from typing import List, Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build
from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi

from eightify.types import VideoComment, VideoDetails, VideoTranscript

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def get_video_details(video_id: str) -> Optional[VideoDetails]:
    logger.debug(f"Getting video details for {video_id}")

    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()

    if response["items"]:
        item = response["items"][0]
        return VideoDetails(
            title=item["snippet"]["title"],
            description=item["snippet"]["description"],
        )

    logger.error(f"No video details found for {video_id}")
    return None


def get_video_transcript(video_id: str) -> Optional[VideoTranscript]:
    logger.debug(f"Getting video transcript for {video_id}")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript])
        return VideoTranscript(text=transcript_text)

    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        return None


def get_video_comments(video_id: str, max_results: int = 100) -> List[VideoComment]:
    logger.debug(f"Getting video comments for {video_id}")
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        order="relevance",  # This sorts comments by relevance
    )
    response = request.execute()

    if not response["items"]:
        logger.error(f"No video comments found for {video_id}")
        return []

    return [
        VideoComment(text=item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]) for item in response["items"]
    ]
