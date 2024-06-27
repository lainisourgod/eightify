import os

from anthropic import Anthropic
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

from eightify.types import VideoComment

load_dotenv(override=True)

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
if LLM_MODEL.startswith("claude"):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
else:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


MIN_NUMBER_OF_COMMENTS = 10


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

    For each key point:
    1. Start with a relevant emoji
    2. Provide a concise summary with specific details or examples
    3. Include a brief, impactful quote if available
    4. If possible, mention an approximate timestamp or section of the video where this point is discussed (e.g., "early in the video", "around the middle", "towards the end")

    Focus on:
    - 💡 Main ideas and key concepts
    - 🔍 New or potentially unfamiliar topics for the viewer
    - 🔑 Practical implications and real-world applications
    - 🧠 Unique theories or perspectives presented
    - 💬 Questions that arise from the content that a viewer might want to ask the creator
    - 📌 Calls to action or viewer engagement elements

    After the key points, include a section titled "💬 Potential Questions for the Creator" with 2-3 thought-provoking questions based on the content.

    Transcript:
    {transcript}

    If the transcript is too short or unsuitable for this type of analysis, please indicate this in your response.
    """


def create_comment_analysis_prompt(
    comments: list[VideoComment], video_summary: str | None = None, insight_request: str | None = None
) -> str:
    COMMENT_SEPARATOR = "|||"
    comment_text = COMMENT_SEPARATOR.join(comment.text for comment in comments)

    base_prompt = f"""
    Analyze the following YouTube video comments. The comments are separated by '{COMMENT_SEPARATOR}'.

    Your goal is to provide valuable insights that solve these user problems:
    - Finding unique insights without diving into a "rabbit hole" of comments
    - Identifying discussions about specific topics of interest
    - Discovering potential questions for the video creator
    - Understanding the community's reaction and engagement

    Provide insights on:
    - 🔑 Common themes or topics discussed
    - 😊 Overall sentiment trends
    - 💡 Unique or interesting perspectives
    - ❓ Recurring questions or concerns
    - 🛠️ Constructive feedback or suggestions

    Guidelines:
    - Structure your response with clear headings for each major insight
    - Use bullet points for multiple points under each heading
    - Start each heading with a relevant emoji
    - Include brief, impactful quotes from comments to support your analysis
    - Use _italic_ and **bold** for emphasis in longer sentences
    - Be concise and direct, focusing on valuable insights
    - Avoid filler phrases or unnecessary judgments

    After the main analysis, include a section titled "📌 Potential Follow-up Topics" with 2-3 ideas based on comment discussions that could be interesting for future content.

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

    base_prompt += f"""
    Comments:
    {comment_text}

    If the comments are too few or unsuitable for this type of analysis, please indicate this in your response.
    """

    return base_prompt


def get_llm_response(system_prompt: str, user_prompt: str) -> str | None:
    """
    Get a response from the language model using either Anthropic or OpenAI client.
    """
    if isinstance(client, Anthropic):
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    elif isinstance(client, OpenAI):
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    else:
        raise ValueError("Invalid client type. Please use Anthropic or OpenAI.")


def summarize_text(
    text: str,
    video_title: str,
    video_description: str,
    max_points: int = 3,
    max_length: int = 500,
) -> str | None:
    """
    Summarize a YouTube video transcript.
    """
    cropped_text = text[:max_length]
    system_prompt = create_system_prompt()
    user_prompt = create_summary_prompt(video_title, video_description, cropped_text, max_points)

    logger.debug(
        f"Prompt from summarize_text: {user_prompt[:500]}...{user_prompt[-500:]}"
        if len(user_prompt) > 1000
        else f"Prompt from summarize_text: {user_prompt}"
    )

    return get_llm_response(client, system_prompt, user_prompt)


def analyze_comments(
    comments: list[VideoComment],
    video_summary: str | None = None,
    insight_request: str | None = None,
) -> str | None:
    """
    Analyze YouTube video comments and provide insights.
    """
    # Doesn't make sense to make a review for this, the user can just check them.
    if len(comments) < MIN_NUMBER_OF_COMMENTS:
        return None

    system_prompt = create_system_prompt()
    user_prompt = create_comment_analysis_prompt(comments, video_summary, insight_request)

    logger.debug(
        f"Prompt from analyze_comments: {user_prompt[:500]}...{user_prompt[-500:]}"
        if len(user_prompt) > 1000
        else f"Prompt from analyze_comments: {user_prompt}"
    )

    return get_llm_response(client, system_prompt, user_prompt)
