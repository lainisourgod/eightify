import json

from loguru import logger

from eightify.api.llm.base import create_system_prompt, get_llm_response, log_prompt
from eightify.common import CommentAnalysis, CommentTopic, VideoComment, VideoDetails
from eightify.config import config


def create_comment_analysis_prompt(
    video_details: VideoDetails,
    comments: list[VideoComment],
    video_summary: str | None = None,
    insight_request: str | None = None,
    max_topics: int = 5,
) -> str:
    """

    TODO: ask it to also find some very interesting but not common comments.
          like an "insightful" one, surpising. make another topic for it
    TODO: maybe we can create a few predefined topics for such cases
    TODO: make sure it's not using shit comments as "suprising" and "insightful"
    """
    base_prompt = f"""
    Analyze the comments for the following YouTube video:
    Title: {video_details.title}
    Description: {video_details.description}

    Your task is to:
    1. Generate {max_topics} distinct topics that best represent the main themes in the comments.
    2. Assign each comment to one or more relevant topics.
    3. Offer a concise analysis (TLDR) focusing on the most intriguing aspects of the comments.

    Your task:
    1. Find {max_topics} surprising or unique insights from the comments.
    2. For each insight, give a real comment example.
    3. Write a short, simple TLDR of the most interesting stuff you found.

    Rules:
    - Don't talk about general sentiment, engagement, or if people liked the video.
    - Focus on specific, unexpected things people said or asked.
    - Look for ideas that disagree with the video or each other.
    - Highlight any cool ways people used or changed the video's advice.
    - Point out any big questions that weren't answered in the video.
    - Use simple, everyday language. No fancy words.
    - If you can't find {max_topics} really interesting things, just share what you have.

    {f"Video summary for context: {video_summary}" if video_summary else ""}
    {f"User wants to know about: {insight_request}" if insight_request else ""}


    Comments:
    {" ".join(f"Comment {i}: {comment.text}" for i, comment in enumerate(comments))}

    Provide your response as a JSON object with the following structure:
    {{
        "topics": [
            {{
                "name": "Short, simple description of a surprise or unique thing",
                "description": "Brief description of the topic",
                "comment_indices": [0, 1, 2]
            }}
        ],
        "overall_analysis": "2-3 simple sentences about the most interesting stuff you found. Don't mention likes or overall feelings.",
    }}
    """
    return base_prompt


def analyze_and_cluster_comments(
    comments: list[VideoComment],
    video_details: VideoDetails,
    summary: str | None = None,
    insight_request: str | None = None,
) -> CommentAnalysis | None:
    """
    Analyze YouTube video comments, generate topics, and assign comments to topics.
    """
    if len(comments) < config.min_number_of_comments:
        return None

    system_prompt = create_system_prompt()
    user_prompt = create_comment_analysis_prompt(
        video_details=video_details,
        video_summary=summary,
        insight_request=insight_request,
        comments=comments,
        max_topics=config.max_number_of_topics,
    )

    log_prompt(user_prompt, "analyze_and_cluster_comments")

    function_schema = {
        "name": "analyze_and_cluster_comments",
        "description": "Analyze YouTube video comments, generate topics, and assign comments to topics",
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "comment_indices": {"type": "array", "items": {"type": "integer"}},
                        },
                        "required": ["name", "description", "comment_indices"],
                    },
                },
                "overall_analysis": {
                    "type": "string",
                    "description": "Overall analysis of the comments and topics",
                },
            },
            "required": ["topics", "overall_analysis"],
        },
    }

    response = get_llm_response(system_prompt, user_prompt, function_schema)

    if response:
        try:
            analysis_data = json.loads(response)
            return CommentAnalysis(
                comments=comments,
                overall_analysis=analysis_data["overall_analysis"],
                topics=[
                    CommentTopic(
                        name=topic["name"],
                        description=topic["description"],
                        comment_indices=topic["comment_indices"],
                    )
                    for topic in analysis_data["topics"]
                ],
            )
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from LLM")
            return None
    return None
