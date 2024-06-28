import json
from typing import TypedDict

from anthropic import Anthropic
from loguru import logger
from openai import OpenAI

from eightify.config import config
from eightify.types import VideoComment, VideoDetails, VideoTranscript

if config.llm_model.startswith("claude"):
    client = Anthropic(api_key=config.anthropic_key.get_secret_value())
else:
    client = OpenAI(api_key=config.openai_api_key.get_secret_value())


class SummaryPoint(TypedDict):
    emoji: str
    title: str
    content: str
    quote: str
    timestamp: str


class SummaryFunction(TypedDict):
    name: str
    description: str
    parameters: dict


class CommentInsight(TypedDict):
    emoji: str
    title: str
    content: str
    quotes: list[str]


class FollowUpTopic(TypedDict):
    topic: str
    reason: str


class CommentAnalysis(TypedDict):
    insights: list[CommentInsight]
    follow_up_topics: list[FollowUpTopic]


def create_system_prompt() -> str:
    """
    In this system prompt I try to capture the essence of our product and prompt the LLM to act
    as if it was I behind it doing its work the way I would do it.
    """

    return """
    GOAL
    You are an AI assistant in an app called Eightify. Our features description
    - Save time on long videos, get key ideas instantly
    - Eightify helps when you're swamped with too much content
    - It’s an AI YouTube tool which finds the key points in topics like AI, Business, Finance, News, or Health
    - Eightify boosts your learning.
    - Navigate through videos with ease using summarized paragraphs with timestamps.
    - Get the pivotal points and key ideas from the video.
    - Grasp the gist of any video in seconds with our YouTube summary AI.
    - Access translations of summaries in your preferred language. No more language barriers with Eightify.
    You are specialized in analyzing YouTube content, including video transcripts and comments. Your primary goal is to solve the following problem for the user:

    USER PROBLEMS SOLVED
    Always keep the user's core needs in mind: quick understanding, identification of novel content, potential questions, and key timestamps.
    - "Is this worth watching? Will it give anything new for me?"
    - "There's always some unique insights in the comments, but I don't want to dive again in the rabbit hole of the comments when I wanted to go sleep 3 hours ago."
    - "I want to understand what the video is about before diving in"
    - "Do they discuss this one thing I wanted to ask her about myself?"
    - "Where in the video do they talk about it? Timestamps are rarely descriptive enough for me to find what I want."
    - "I don't wanna copypaste the transcript to chatgpt and talk with it there, just provide me with the insights I need right away."
    - " I'm a big fan so far - I'm in the middle of a ton of research and I also watch some of the big name productivity/health accounts, and I use Eightify for almost every video.
        Super convenient to have timestamps so I know where specific topics were mentioned, and if I save the video to my note-taking app, I bring the summary and key points from Eightify along with it."
    - " In the course of 10 minutes, I have generated and read summaries a few hours of video. For those who use YouTube as an information source like me, this is a real game changer and time saver.
        It especially helps when you're not sure if a video is worth the time to watch. The bullet point summaries are easy and fast to read. This will be in my toolbox from now on."

    TASKS
    Your tasks include summarizing videos and providing insights from comments. Your analysis should be:
    - Concise and direct, focusing on key ideas and valuable insights
    - Structured with clear headings and bullet points
    - Enhanced with relevant emojis for readability and engagement
    - Formatted using markdown for better presentation. If you're writing a long sentence, use _italic_ and **bold** for emphasis.
    - Supported by brief quotes when applicable
    - Free from filler phrases or unnecessary judgments

    TONE OF VOICE
    - Be a friendly, helpful assistant that is easy to talk to.
    - Don't make things up.
    - Don't be boring.
    - Don't be too friendly, solve the task.
    - Don't waste time, save it.
    """


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


def create_comment_analysis_prompt(
    video_details: VideoDetails,
    video_summary: str | None = None,
    insight_request: str | None = None,
) -> str:
    base_prompt = f"""
    Analyze the comments for the following YouTube video:
    Title: {video_details.title}
    Description: {video_details.description}

    Your goal is to provide valuable insights that solve these user problems:
    - Finding unique insights without diving into a "rabbit hole" of comments
    - Identifying discussions about specific topics of interest
    - Discovering potential questions for the video creator
    - Understanding the community's reaction and engagement

    Focus on:
    - Common themes or topics discussed
    - Overall sentiment trends
    - Unique or interesting perspectives
    - Recurring questions or concerns
    - Constructive feedback or suggestions

    Be concise and direct, focusing on valuable insights. Avoid filler phrases or unnecessary judgments.
    """

    if video_summary:
        base_prompt += f"""
        Consider this summary of the video content for context:
        {video_summary}

        Relate your comment analysis to the video content where applicable, highlighting any discrepancies or additional insights provided by commenters.
        """

    if insight_request:
        base_prompt += f"""
        User's specific insight request: "{insight_request}"
        Prioritize information relevant to this request in a dedicated section.
        Analyze how the comments relate to or discuss this specific topic.
        """

    return base_prompt


def get_llm_response(system_prompt: str, user_prompt: str, function_schema: SummaryFunction) -> str | None:
    """
    Get a response from the language model using either Anthropic or OpenAI client.
    """
    try:
        if isinstance(client, Anthropic):
            # Anthropic doesn't support function calling in the same way as OpenAI
            # You might need to modify the prompt to include the function schema
            response = client.messages.create(
                model=config.llm_model,
                max_tokens=1000,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        elif isinstance(client, OpenAI):
            response = client.chat.completions.create(
                model=config.llm_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                functions=[function_schema],
                function_call={"name": function_schema["name"]},
            )
            return response.choices[0].message.function_call.arguments
        else:
            raise ValueError("Invalid client type. Please use Anthropic or OpenAI.")
    except Exception as e:
        logger.error(f"Error in get_llm_response: {str(e)}")
        return None


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


def analyze_comments(
    comments: list[VideoComment],
    video_details: VideoDetails,
    summary: str | None = None,
    insight_request: str | None = None,
    transcript: VideoTranscript | None = None,
) -> str | None:
    """
    Analyze YouTube video comments and provide insights.
    """
    # Doesn't make sense to make a review for this, the user can just check them.
    if len(comments) < config.min_number_of_comments:
        return None

    system_prompt = create_system_prompt()
    user_prompt = create_comment_analysis_prompt(
        video_details=video_details,
        video_summary=summary,
        insight_request=insight_request,
    )

    comment_text = "\n".join(f"Comment {i + 1}: {comment.text}" for i, comment in enumerate(comments))
    user_prompt += f"\n\nComments:\n{comment_text}"

    log_prompt(user_prompt, "analyze_comments")

    function_schema = {
        "name": "analyze_video_comments",
        "description": "Analyze YouTube video comments and provide insights",
        "parameters": {
            "type": "object",
            "properties": {
                "insights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "emoji": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "quotes": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["emoji", "title", "content", "quotes"],
                    },
                },
                "follow_up_topics": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"topic": {"type": "string"}, "reason": {"type": "string"}},
                        "required": ["topic", "reason"],
                    },
                },
            },
            "required": ["insights", "follow_up_topics"],
        },
    }

    response = get_llm_response(system_prompt, user_prompt, function_schema)

    if response:
        try:
            analysis_data = json.loads(response)
            formatted_analysis = format_comment_analysis(analysis_data)
            return formatted_analysis
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse JSON response from LLM")
            return None
    return None


def format_summary(summary_data: list[SummaryPoint]) -> str:
    """
    Format the JSON summary data into a readable string.
    """
    formatted_summary = "**Key Points**\n\n"
    for i, point in enumerate(summary_data, 1):
        formatted_summary += (
            f"{i}. {point['emoji']} **{point['title']}:** {point['content']} "
            f"*\"{point['quote']}\"* ({point['timestamp']})\n\n"
        )
    return formatted_summary.strip()


def format_comment_analysis(analysis_data: CommentAnalysis) -> str:
    """
    Format the JSON comment analysis data into a readable string.
    """
    formatted_analysis = "**Comment Analysis**\n\n"

    for insight in analysis_data["insights"]:
        formatted_analysis += f"{insight['emoji']} **{insight['title']}**\n" f"{insight['content']}\n"
        if insight["quotes"]:
            for quote in insight["quotes"]:
                formatted_analysis += f"> {quote}\n"
        formatted_analysis += "\n"

    formatted_analysis += "**📌 Potential Follow-up Topics**\n\n"
    for topic in analysis_data["follow_up_topics"]:
        formatted_analysis += f"- **{topic['topic']}**: {topic['reason']}\n"

    return formatted_analysis.strip()


def log_prompt(prompt: str, prompt_name: str) -> None:
    if len(prompt) > config.log_prompt_length:
        half_length = config.log_prompt_length // 2
        message = f"Prompt from {prompt_name}: {prompt[:half_length]}\n🙈...🙈\n{prompt[-half_length:]}"
    else:
        message = f"Prompt from {prompt_name}: {prompt}"
    logger.debug(message)
