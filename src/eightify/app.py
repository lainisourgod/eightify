import html
import re

import requests
import streamlit as st

from eightify.api.youtube import get_video_comments, get_video_details, get_video_transcript
from eightify.types import VideoComment
from eightify.utils import extract_video_id

APP_HOST = "http://localhost:8000"


def main():
    st.set_page_config(page_title="Eightify", page_icon="🍓")

    url = st.text_input("Enter YouTube video URL:")

    if url is not None:
        video_id = extract_video_id(url)
        if video_id:
            try:
                process_video(video_id)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.error("Invalid YouTube URL. Please enter a valid URL.")

    display_sidebar_info()


def process_video(video_id):
    # Fetch video details
    video_details = get_video_details(video_id)

    if not video_details:
        st.error("No video details found.")
        st.stop()

    # Display video title and embed
    st.subheader(video_details.title)
    st.video(f"https://www.youtube.com/embed/{video_id}")

    # Fetch transcript
    transcript = get_video_transcript(video_id)

    if not transcript:
        st.error("No transcript found.")
        st.stop()

    # Generate summary
    with st.spinner("Generating summary..."):
        summary_response = requests.post(
            f"{APP_HOST}/summarize",
            json={"video_id": video_id},
        ).json()

    # Display summary
    st.subheader("Summary")
    st.write(summary_response["summary"])

    # Fetch and analyze comments
    # TODO: insight request
    with st.spinner("Analyzing comments..."):
        comments = get_video_comments(video_id)
        comment_analysis_response = requests.post(
            f"{APP_HOST}/analyze_comments",
            json={"video_id": video_id},
        ).json()

    # Display comment analysis
    display_comment_analysis(comments, comment_analysis_response["comment_analysis"])


def display_comment_analysis(comments: list[VideoComment], comment_analysis: str):
    st.subheader("Comments")
    with st.expander("Show Comments"):
        for comment in comments:
            # Parse HTML-like tags to Markdown
            parsed_comment = comment.text
            parsed_comment = parsed_comment.replace("<br>", "\n")
            parsed_comment = re.sub(r"<i>(.*?)</i>", r"*\1*", parsed_comment)
            parsed_comment = re.sub(r"<b>(.*?)</b>", r"**\1**", parsed_comment)
            parsed_comment = re.sub(r"<strike>(.*?)</strike>", r"~~\1~~", parsed_comment)

            st.write(parsed_comment)
            st.write("---")  # Add a separator between comments

    st.subheader("Comment Analysis")
    st.write(comment_analysis)


def display_sidebar_info():
    st.sidebar.title("About")
    st.sidebar.info("🍓 Hello! Eightify is a tool to quickly gain insights from YouTube videos. Relax and enjoy!")


if __name__ == "__main__":
    main()
