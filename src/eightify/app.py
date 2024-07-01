import re

import requests
import streamlit as st

from eightify.api.youtube import get_video_details, get_video_transcript
from eightify.common import CommentAnalysis, VideoComment, VideoDetails
from eightify.config import config
from eightify.utils import extract_video_id


@st.cache_data
def fetch_video_details(video_id: str) -> VideoDetails | None:
    return get_video_details(video_id)


def make_api_request(endpoint: str, data: dict, timeout: int = 60) -> dict | None:
    try:
        response = requests.post(
            f"{config.backend_url}/{endpoint}",
            json=data,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.write("Request timed out. The server might be busy. Please try again later. 🕒")
    except requests.exceptions.RequestException as e:
        st.write(f"An error occurred while communicating with the API: {str(e)} 🙇")
    return None


@st.cache_data
def summarize_transcript(video_id: str) -> str | None:
    result = make_api_request("summarize", {"video_id": video_id})
    return result.get("summary") if result else None


@st.cache_data
def analyze_comments(video_id: str, insight_request: str) -> CommentAnalysis | None:
    result = make_api_request("analyze_comments", {"video_id": video_id, "insight_request": insight_request})
    return CommentAnalysis(**result) if result else None


def display_raw_comments(comments: list[VideoComment]):
    with st.expander("Show Comments"):
        for comment in comments:
            parsed_comment = re.sub(r"<i>(.*?)</i>", r"*\1*", comment.text)
            parsed_comment = re.sub(r"<b>(.*?)</b>", r"**\1**", parsed_comment)
            parsed_comment = re.sub(r"<strike>(.*?)</strike>", r"~~\1~~", parsed_comment)
            parsed_comment = parsed_comment.replace("<br>", "\n")
            st.write(parsed_comment)
            st.write("---")


def make_shorter_if_long(text: str, max_length: int) -> str:
    return text[:max_length] + "..." if len(text) > max_length else text


def set_state(i):
    st.session_state.stage = i


def display_sidebar_info():
    st.sidebar.title("About")
    st.sidebar.info("🍓 Hello! Eightify is a tool to quickly gain insights from YouTube videos. Relax and enjoy!")


def display_topic_comments(topic_comments):
    comment_cols = st.columns(5)
    for j, comment in enumerate(topic_comments):
        with comment_cols[j % 5]:
            st.markdown(
                f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                    <small>{comment.text}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main():
    st.set_page_config(page_title="Eightify", page_icon="🍓", layout="wide")
    display_sidebar_info()

    if "stage" not in st.session_state:
        st.session_state.stage = 0

    if st.session_state.stage == 0:
        st.button("Start", on_click=set_state, args=[1])

    if st.session_state.stage >= 1:
        youtube_url = st.text_input(
            "Enter YouTube Video URL (only English language for now):", on_change=set_state, args=[2]
        )

    if st.session_state.stage >= 2:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            st.error("Invalid YouTube URL.")
            st.stop()

        video_details = fetch_video_details(video_id)
        if not video_details:
            st.error(f"Can't fetch video details for {video_id}.")
            st.stop()

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader(make_shorter_if_long(video_details.title, 150))
            st.video(f"https://www.youtube.com/embed/{video_id}")

            if not st.session_state.get("summary"):
                with st.spinner("Summarizing video..."):
                    transcript = get_video_transcript(video_id)
                    if not transcript:
                        st.error("No transcript found. Probably it's not in English 😒")
                        set_state(0)
                        st.stop()
                    transcript = transcript.points

                    summary = summarize_transcript(video_id)

                st.session_state.summary = summary
                st.session_state.transcript = transcript

            # TODO: transcript is shown twice
            with st.expander("Show Full Transcript"):
                st.write(st.session_state.transcript)

        with col2:
            st.header("✨ Summary")
            st.write(st.session_state.summary)

        st.header("💭 Comment Analysis")

        col1, col2 = st.columns(2)
        with col1:
            insight_request = st.text_input(
                "Enter insight to find in comments (optional):", on_change=set_state, args=[3]
            )

        with col2:
            # Add padding to the button accomodate for text input label height
            vert_space = '<div style="padding: 13.5px 5px;"></div>'
            st.markdown(vert_space, unsafe_allow_html=True)
            if st.button("Analyze Comments"):
                set_state(3)

        if st.session_state.stage >= 3:
            with st.spinner("Analyzing comments..."):
                comment_analysis = analyze_comments(video_id, insight_request)
                if comment_analysis is None:
                    st.error("No comments found.")
                    set_state(2)
                    st.stop()

            st.subheader("📌 TLDR")
            st.write(comment_analysis.overall_analysis)

            st.subheader("👀 Comment Topics")
            topic_buttons = st.columns(len(comment_analysis.topics))

            for i, (topic, col) in enumerate(zip(comment_analysis.topics, topic_buttons)):
                with col:
                    if st.button(f"{i + 1}. {topic.name}", key=f"topic_{i}"):
                        st.session_state.selected_topic = i

            if "selected_topic" in st.session_state:
                i = st.session_state.selected_topic
                topic = comment_analysis.topics[i]

                topic_comments = [
                    comment_analysis.comments[comment_index]
                    for comment_index in comment_analysis.topics[i].comment_indices
                ]

                if topic_comments:
                    display_topic_comments(topic_comments)

        st.button("Start Over", on_click=set_state, args=[0])


if __name__ == "__main__":
    main()
