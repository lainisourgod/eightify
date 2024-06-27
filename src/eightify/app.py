import re

import requests
import streamlit as st

from eightify.api.youtube import get_video_comments, get_video_details, get_video_transcript
from eightify.types import VideoComment
from eightify.utils import extract_video_id

APP_HOST = "http://localhost:8000"


def display_video_details(video_id):
    video_details = get_video_details(video_id)

    if not video_details:
        st.error("No video details found.")
        st.stop()

    st.subheader(video_details.title)
    st.video(f"https://www.youtube.com/embed/{video_id}")


def summarize_transcript(video_id: str) -> str:
    summary_response = requests.post(
        f"{APP_HOST}/summarize",
        json={"video_id": video_id},
    ).json()
    return summary_response.get("summary")


def analyze_comments(video_id: str, insight_request: str) -> str:
    response = requests.post(
        f"{APP_HOST}/analyze_comments",
        json={"video_id": video_id, "insight_request": insight_request},
    ).json()
    return response.get("comment_analysis")


def display_comments(comments: list[VideoComment]):
    with st.expander("Show Comments"):
        for comment in comments:
            parsed_comment = re.sub(r"<i>(.*?)</i>", r"*\1*", comment.text)
            parsed_comment = re.sub(r"<b>(.*?)</b>", r"**\1**", parsed_comment)
            parsed_comment = re.sub(r"<strike>(.*?)</strike>", r"~~\1~~", parsed_comment)
            parsed_comment = parsed_comment.replace("<br>", "\n")
            st.write(parsed_comment)
            st.write("---")


def set_state(i):
    st.session_state.stage = i
    # st.session_state.step += 1
    # st.write(f"{st.session_state.step}. State set to: {i}")  # Debug statement


def display_sidebar_info():
    st.sidebar.title("About")
    st.sidebar.info("🍓 Hello! Eightify is a tool to quickly gain insights from YouTube videos. Relax and enjoy!")


def main():
    st.set_page_config(page_title="Eightify", page_icon="🍓")
    display_sidebar_info()

    if "stage" not in st.session_state:
        st.session_state.stage = 0
        # Step is a debug variable
        # st.session_state.step = 0

    if st.session_state.stage == 0:
        st.button("Start", on_click=set_state, args=[1])

    if st.session_state.stage >= 1:
        # Input for YouTube URL
        youtube_url = st.text_input(
            "Enter YouTube Video URL (only English language for now):", on_change=set_state, args=[2]
        )

    if st.session_state.stage >= 2:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            st.error("Invalid YouTube URL.")
            st.stop()

        video_details = get_video_details(video_id)
        if not video_details:
            st.error(f"Can't fetch video details for {video_id}.")
            st.stop()

        st.subheader(video_details.title)
        st.video(f"https://www.youtube.com/embed/{video_id}")

        # Get and summarize transcript
        if not st.session_state.get("summary"):
            with st.spinner("Summarizing video..."):
                transcript = get_video_transcript(video_id)
                if not transcript:
                    st.error("No transcript found. Probably it's not in English 😒")
                    set_state(0)
                    exit()
                transcript = transcript.points

                summary = summarize_transcript(video_id)
            st.session_state.summary = summary
            st.session_state.transcript = transcript

        st.header("Summary")
        st.write(st.session_state.summary)
        with st.expander("Show Full Transcript"):
            st.write(st.session_state.transcript)

        insight_request = st.text_input("Enter insight to find in comments (optional):", on_change=set_state, args=[3])
        st.button("Analyze Comments", on_click=set_state, args=[3])

    if st.session_state.stage >= 3:
        with st.spinner("Analyzing comments..."):
            comments = get_video_comments(video_id)
            comment_analysis = analyze_comments(video_id, insight_request)

        st.header("Comment Analysis")
        display_comments(comments)

        st.write(comment_analysis)

        st.button("Start Over", on_click=set_state, args=[0])


if __name__ == "__main__":
    main()
