import os

import anthropic
import openai
from dotenv import load_dotenv
from loguru import logger

from eightify.types import VideoComment

load_dotenv(override=True)

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
if LLM_MODEL.startswith("claude"):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
else:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_text(
    text: str,
    video_title: str,
    video_description: str,
    max_points: int = 3,
    max_length: int = 500,
) -> str | None:
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
    2. Provide a concise, direct summary of the idea. Include specific details, examples, or analogies from the transcript.
    3. If available, include a brief, impactful quote that reinforces the point.

    Guidelines:
    - Focus on the main ideas, key concepts, and any unique theories presented.
    - Highlight practical implications or real-world applications of the ideas.
    - Capture the tone and style of the content without explicitly analyzing it.
    - Include any call to action or viewer engagement elements mentioned.
    - Avoid filler phrases like "the video explores" or "viewers are encouraged to."
    - Be specific and clear in your language, avoiding vague statements.
    - If a point seems speculative or unclear, omit it rather than using phrases like "likely" or "might."
    - Group related points together for better readability.
    - Ensure the summary reflects both the content and the presentation style of the video.
    - Use markdown for readability formatting.
    
    Transcript:
    {cropped_text}
    """
    system_prompt = "You are a helpful assistant that summarizes YouTube video transcripts."

    # Log the prompt, cropping the middle part if too long
    if len(prompt) > 1000:
        logger.debug(f"Prompt from summarize_text: {prompt[:500]}...{prompt[-500:]}")
    else:
        logger.debug(f"Prompt from summarize_text: {prompt}")

    if isinstance(client, anthropic.Anthropic):
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text
    else:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        answer = response.choices[0].message.content

    return answer


def analyze_comments(comments: list[VideoComment], insight_request: str | None = None) -> str | None:
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
    6. Specific insights related to the user's request (if provided)
    
    Provide a concise analysis that captures the most valuable insights from these comments.
    Structure your response with clear headings for each point. Don't group by focus areas,
    but rather use them as guidelines to look for.
    Don't include any filler phrases like "the video explores" or "viewers are encouraged to."
    Don't make a point "questions raised by viewers". If there's an interesting or repeating question, just show it.
    Use bullet points for listing multiple insights under each heading.
    Start with a relevant emoji that captures the essence of the point.
    Use markdown and prepend every line with emoji for readability formatting.
    If applicable, include brief quotes from comments to support your analysis.
    Don't make an overall judgment about the comments.
    """
    system_prompt = "You are a helpful assistant that analyzes YouTube video comments to provide valuable insights, with a focus on user-specified requests when provided."

    if insight_request:
        specific_prompt = f"""
        User's insight request: 
        "{insight_request}"

        Prioritize information relevant to the user's request. Dedicate a separate section to address this specific insight.
        Analyze how the comments relate to or discuss the requested topic.
        Include examples or trends from the comments that are particularly relevant to this request.
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

    if isinstance(client, anthropic.Anthropic):
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": full_prompt}],
        )
        answer = response.content[0].text
    else:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt},
            ],
        )
        answer = response.choices[0].message.content

    return answer
