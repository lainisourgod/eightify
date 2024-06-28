import json
from typing import TypedDict

from loguru import logger

from eightify.api.llm.base import create_system_prompt, get_llm_response, log_prompt
from eightify.common import CommentAnalysis, CommentAssignment, CommentTopic, VideoComment, VideoDetails
from eightify.config import config


class CommentInsightFunctionType(TypedDict):
    emoji: str
    title: str
    content: str
    quotes: list[str]


class FollowUpTopicFunctionType(TypedDict):
    topic: str
    reason: str


class CommentAnalysisFunctionType(TypedDict):
    insights: list[CommentInsightFunctionType]
    follow_up_topics: list[FollowUpTopicFunctionType]


# TODO: ask it to also find some very interesting but not common comments
# like an "insightful" one, surpising. make another topic for it
# TODO: maybe we can create a few predefined topics for such cases
# TODO: make sure it's not using shit comments as "suprising" and "insightful"


def create_comment_analysis_prompt(
    video_details: VideoDetails,
    comments: list[VideoComment],
    video_summary: str | None = None,
    insight_request: str | None = None,
) -> str:
    base_prompt = f"""
    Analyze the comments for the following YouTube video:
    Title: {video_details.title}
    Description: {video_details.description}

    Your task is to:
    1. Generate 5 distinct topics that best represent the main themes in the comments.
    2. Assign each comment to one of these topics.
    3. Provide an overall analysis of the comments and topics.

    Guidelines:
    - Topics should be concise but descriptive.
    - Each comment should be assigned to the most relevant topic.
    - In the overall analysis, focus on valuable insights, sentiment trends, and unique perspectives.

    {f"Video summary for context: {video_summary}" if video_summary else ""}
    {f"User's specific insight request: {insight_request}" if insight_request else ""}

    Comments:
    {" ".join(f"Comment {i}: {comment.text}" for i, comment in enumerate(comments))}

    Provide your response as a JSON object with the following structure:
    {{
        "topics": [
            {{"name": "Topic Name", "description": "Brief description of the topic"}}
        ],
        "comment_assignments": [
            {{"comment_index": 0, "topic_index": 0}}
        ],
        "overall_analysis": "Your overall analysis of the comments and topics"
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
        video_details=video_details, video_summary=summary, insight_request=insight_request, comments=comments
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
                        },
                        "required": ["name", "description"],
                    },
                },
                "comment_assignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "comment_index": {"type": "integer"},
                            "topic_index": {"type": "integer"},
                        },
                        "required": ["comment_index", "topic_index"],
                    },
                },
                "overall_analysis": {
                    "type": "string",
                    "description": "Overall analysis of the comments and topics",
                },
            },
            "required": ["topics", "comment_assignments", "overall_analysis"],
        },
    }

    response = get_llm_response(system_prompt, user_prompt, function_schema)

    if response:
        try:
            analysis_data = json.loads(response)
            return CommentAnalysis(
                topics=[CommentTopic(**topic) for topic in analysis_data["topics"]],
                comment_assignments=[
                    CommentAssignment(**assignment) for assignment in analysis_data["comment_assignments"]
                ],
                comments=comments,
                overall_analysis=analysis_data["overall_analysis"],
            )
            # return format_comment_analysis(analysis_data)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from LLM")
            return None
    return None


# def format_comment_analysis(analysis_data: dict) -> str:
#     """
#     Format the JSON comment analysis data into a readable string.
#     """
#     formatted_analysis = "**Comment Analysis**\n\n"

#     # Format topics and their comments
#     for i, topic in enumerate(analysis_data["topics"]):
#         formatted_analysis += f"{i + 1}. **{topic['name']}**\n"
#         formatted_analysis += f"   {topic['description']}\n\n"

#         # Find comments assigned to this topic
#         topic_comments = [comment for comment in analysis_data["comment_assignments"] if comment["topic_index"] == i]

#         if topic_comments:
#             formatted_analysis += "   Sample comments:\n"
#             for comment in topic_comments[:3]:  # Limit to 3 sample comments per topic
#                 comment_text = analysis_data["comments"][comment["comment_index"]].text
#                 formatted_analysis += f"   > {comment_text[:100]}...\n"  # Truncate long comments

#         formatted_analysis += "\n"

#     # Format overall analysis
#     formatted_analysis += "**Overall Analysis**\n\n"
#     formatted_analysis += f"{analysis_data['overall_analysis']}\n\n"

#     # You can still include follow-up topics if they're part of your new structure
#     if "follow_up_topics" in analysis_data:
#         formatted_analysis += "**📌 Potential Follow-up Topics**\n\n"
#         for topic in analysis_data["follow_up_topics"]:
#             formatted_analysis += f"- **{topic['topic']}**: {topic['reason']}\n"

#     return formatted_analysis.strip()
