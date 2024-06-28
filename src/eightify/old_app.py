import re

import requests
import streamlit as st

from eightify.api.youtube import get_video_comments, get_video_details, get_video_transcript
from eightify.common import VideoComment
from eightify.utils import extract_video_id

APP_HOST = "http://localhost:8000"


def main():
    st.set_page_config(page_title="Eightify", page_icon="🍓")
    display_sidebar_info()

    st.text_input("Enter YouTube video URL:", on_change=process_url_change, key="youtube_url")

    if "video_id" in st.session_state:
        display_video_details(st.session_state.video_id)
        display_summary(st.session_state.video_id)
        display_comments(st.session_state.video_id)


def process_url_change():
    url = st.session_state.youtube_url
    video_id = extract_video_id(url)

    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid URL.")
        return

    st.session_state.video_id = video_id
    st.session_state.video_details_processed = False
    st.session_state.summary_processed = False
    st.session_state.comments_processed = False
    st.session_state.comments = []
    st.session_state.comment_analysis = ""


def display_video_details(video_id):
    if not st.session_state.get("video_details_processed"):
        video_details = get_video_details(video_id)

        if not video_details:
            st.error("No video details found.")
            st.stop()

    st.subheader(video_details.title)
    st.video(f"https://www.youtube.com/embed/{video_id}")


def display_summary(video_id):
    if not st.session_state.get("summary_processed"):
        try:
            summary = process_summary(video_id)
            st.session_state.summary_processed = True
            st.session_state.summary = summary
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    st.subheader("Summary")
    st.write(st.session_state.summary)


def process_summary(video_id: str) -> str:
    transcript = get_video_transcript(video_id)

    if not transcript:
        st.error("No transcript found.")
        st.stop()

    with st.spinner("💭 Generating summary..."):
        summary_response = requests.post(
            f"{APP_HOST}/summarize",
            json={"video_id": video_id},
        ).json()

    return summary_response["summary"]


def display_comments(video_id):
    if not st.session_state.get("comments_processed"):
        st.text_input(
            "If you're interested in a specific topic, enter it here",
            key="insight_request",
            on_change=process_comments,
            args=(video_id,),
        )
        if st.button("👀 Explore comments"):
            process_comments(video_id)

    if st.session_state.get("comments"):
        display_comment_analysis(st.session_state.comments, st.session_state.comment_analysis)


def process_comments(video_id: str):
    insight_request = st.session_state.get("insight_request", "")
    st.subheader("Comment Analysis")

    with st.spinner("💭 Analyzing comments..."):
        comments = get_video_comments(video_id)
        comment_analysis_response = requests.post(
            f"{APP_HOST}/analyze_comments",
            json={"video_id": video_id, "insight_request": insight_request},
        ).json()

    st.session_state.comments = comments
    st.session_state.comment_analysis = comment_analysis_response["comment_analysis"]
    st.session_state.comments_processed = True


def display_comment_analysis(comments: list[VideoComment], comment_analysis: str):
    st.subheader("Comments")

    with st.expander("Show Comments"):
        for comment in comments:
            parsed_comment = re.sub(r"<i>(.*?)</i>", r"*\1*", comment.text)
            parsed_comment = re.sub(r"<b>(.*?)</b>", r"**\1**", parsed_comment)
            parsed_comment = re.sub(r"<strike>(.*?)</strike>", r"~~\1~~", parsed_comment)
            parsed_comment = parsed_comment.replace("<br>", "\n")
            st.write(parsed_comment)
            st.write("---")

    st.subheader("Comment Analysis")
    st.write(comment_analysis)


def display_sidebar_info():
    st.sidebar.title("About")
    st.sidebar.info("🍓 Hello! Eightify is a tool to quickly gain insights from YouTube videos. Relax and enjoy!")


if __name__ == "__main__":
    main()
