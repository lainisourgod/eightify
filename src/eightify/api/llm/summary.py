import json
from typing import TypedDict

from loguru import logger

from eightify.api.llm.base import create_system_prompt, get_llm_response, log_prompt
from eightify.common import VideoTranscript
from eightify.config import config


def create_summary_prompt(video_title: str, video_description: str, transcript: str, max_points: int) -> str:
    return f"""
    Analyze and summarize the following YouTube video transcript in up to {max_points} key points.

    Video Information:
    Title: {video_title}
    Description: {video_description}


    Provide the summary as a JSON array of objects. Each object should have the following structure:
    {{
        "emoji": "Relevant emoji",
        "title": "Bold title (max 5 words)",
        "content": "Concise paragraph combining main idea, practical implications, and examples",
        "quote": "Brief, impactful quote from the video",
        "timestamp": "Approximate timestamp (MM:SS format)"
    }}

    Guidelines:
    - Focus on the most important and unique ideas presented in the video.
    - Keep the content concise, aiming for 2-3 sentences excluding the quote.
    - Use clear, direct language without filler phrases.
    - Ensure each point gives a complete picture of a key idea from the video.
    - Do not include any introductory or concluding sentences in the JSON.

    Transcript:
    {transcript}

    If the transcript is too short or unsuitable for this type of analysis, please indicate this in your response.
    """


def summarize_text(
    transcript: VideoTranscript,
    video_title: str,
    video_description: str,
) -> str | None:
    cropped_text = transcript.text[: config.max_transcript_length]
    system_prompt = create_system_prompt()
    user_prompt = create_summary_prompt(video_title, video_description, cropped_text, config.max_points)

    log_prompt(user_prompt, "summarize_text")

    function_schema = {
        "name": "create_video_summary",
        "description": "Create a summary of a YouTube video with key points",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "emoji": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "quote": {"type": "string"},
                            "timestamp": {"type": "string"},
                        },
                        "required": ["emoji", "title", "content", "quote", "timestamp"],
                    },
                }
            },
            "required": ["summary"],
        },
    }

    response = get_llm_response(system_prompt, user_prompt, function_schema)

    if response:
        try:
            summary_data = json.loads(response)["summary"]
            formatted_summary = format_summary(summary_data)
            return formatted_summary
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse JSON response from LLM")
            return None
    return None


class SummaryPoint(TypedDict):
    emoji: str
    title: str
    content: str
    quote: str


def format_summary(summary_data: list[SummaryPoint]) -> str:
    """
    Format the JSON summary data into a readable string.
    """
    formatted_summary = "**Key Points**\n\n"
    for i, point in enumerate(summary_data, 1):
        formatted_summary += (
            f"{i}. {point['emoji']} **{point['title']}:** {point['content']} " f"*\"{point['quote']}\"* \n\n"
        )
    return formatted_summary.strip()
