import os

import openai
from dotenv import load_dotenv
from loguru import logger

from eightify.types import VideoComment

load_dotenv(override=True)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_text(
    text: str,
    video_title: str,
    video_description: str,
    max_points: int = 10,
    max_length: int = 500,
) -> str:
    """
    Summarize the following YouTube video transcript in up to {max_points} key points.
    Video title and description given as the context to the prompt.
    Crop the input text to the first {max_length} characters for debugging purposes to not
    burn all your credits.
    """
    cropped_text = text[:max_length]  # Crop the input text to the first 1000 characters
    prompt = f"""
    Summarize the following YouTube video transcript in up to {max_points} key points. 
    Video title: {video_title}
    Video description: {video_description}
    
    For each key point:
    1. Start with a relevant emoji that captures the essence of the point.
    2. Provide a concise summary of the idea, including specific details or examples when possible.
    3. If applicable, include a brief, impactful quote from the transcript.

    Focus on:
    1. The main ideas and key concepts, including any theories or analogies used.
    2. Practical implications or real-world applications of these ideas.
    3. The tone and style of the content, including any vivid imagery or emotional language used.
    4. Any call to action or viewer engagement elements.

    Structure the summary to group related points together for better readability.

    Ensure the summary captures both the factual content and the essence of how the ideas are presented in the video.

    Transcript:
    {cropped_text}
    """

    # Log the prompt, cropping the middle part if too long
    if len(prompt) > 1000:
        logger.debug(f"Prompt from summarize_text: {prompt[:500]}...{prompt[-500:]}")
    else:
        logger.debug(f"Prompt from summarize_text: {prompt}")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes YouTube video transcripts.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def analyze_comments(comments: list[VideoComment], insight_request: str | None = None) -> str:
    """
    Analyze the following YouTube video comments and provide insights.
    You can optionally provide a user-specified insight request, prompting AI
    to focus on that aspect in the comments.
    """
    COMMENT_SEPARATOR = "|||"
    comment_text = COMMENT_SEPARATOR.join([comment.text for comment in comments])

    base_prompt = f"""
    Analyze the following YouTube video comments and provide insights. The comments are separated by '{COMMENT_SEPARATOR}'.
    
    Focus on:
    1. Common themes or topics discussed
    2. Overall sentiment (positive, negative, mixed)
    3. Interesting or unique perspectives
    4. Questions or concerns raised by viewers
    5. Any constructive feedback or suggestions
    
    Provide a concise analysis that captures the most valuable insights from these comments.
    """

    if insight_request:
        specific_prompt = f"""
        User's insight request: {insight_request}
        
        Prioritize information relevant to the user's request, but include other valuable insights if found.
        """
        full_prompt = f"{specific_prompt}\n\n{base_prompt}"
    else:
        full_prompt = base_prompt

    full_prompt += f"\n\nComments:\n{comment_text}"

    # Log the prompt, cropping the middle part if too long
    if len(full_prompt) > 1000:
        logger.debug(f"Prompt from analyze_comments: {full_prompt[:500]}...{full_prompt[-500:]}")
    else:
        logger.debug(f"Prompt from analyze_comments: {full_prompt}")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that analyzes YouTube video comments to provide valuable insights, with a focus on user-specified requests when provided.",
            },
            {"role": "user", "content": full_prompt},
        ],
    )
    return response.choices[0].message.content
