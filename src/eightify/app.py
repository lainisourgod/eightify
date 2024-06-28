import re

import requests
import streamlit as st

from eightify.api.youtube import get_video_comments, get_video_details, get_video_transcript
from eightify.common import CommentAnalysis, VideoComment
from eightify.utils import extract_video_id

APP_HOST = "http://localhost:8000"


def display_video_details(video_id):
    video_details = get_video_details(video_id)

    if not video_details:
        st.error("No video details found.")
        st.stop()

    st.subheader(video_details.title)
    st.video(f"https://www.youtube.com/embed/{video_id}")


@st.cache_data
def summarize_transcript(video_id: str) -> str:
    summary_response = requests.post(
        f"{APP_HOST}/summarize",
        json={"video_id": video_id},
    ).json()
    return summary_response.get("summary")


@st.cache_data
def analyze_comments(video_id: str, insight_request: str) -> CommentAnalysis:
    response = requests.post(
        f"{APP_HOST}/analyze_comments",
        json={"video_id": video_id, "insight_request": insight_request},
    ).json()
    return CommentAnalysis(**response)


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


def display_sidebar_info():
    st.sidebar.title("About")
    st.sidebar.info("🍓 Hello! Eightify is a tool to quickly gain insights from YouTube videos. Relax and enjoy!")


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

        video_details = get_video_details(video_id)
        if not video_details:
            st.error(f"Can't fetch video details for {video_id}.")
            st.stop()

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader(video_details.title)
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
            with st.expander("Show Full Transcript"):
                st.write(st.session_state.transcript)

        with col2:
            st.header("Summary")
            st.write(st.session_state.summary)

        st.header("Comment Analysis")
        insight_request = st.text_input("Enter insight to find in comments (optional):", on_change=set_state, args=[3])
        if st.button("Analyze Comments"):
            set_state(3)

        # TODO: move this hard code to the function
        if st.session_state.stage >= 3:
            with st.spinner("Analyzing comments..."):
                comment_analysis = analyze_comments(video_id, insight_request)

            num_topics = len(comment_analysis.topics)
            cols = st.columns(num_topics)

            for i, (topic, col) in enumerate(zip(comment_analysis.topics, cols)):
                with col:
                    st.subheader(f"{i + 1}. {topic.name}")
                    st.write(topic.description)

                    topic_comments = [
                        comment_analysis.comments[ca.comment_index]
                        for ca in comment_analysis.comment_assignments
                        if ca.topic_index == i
                    ]
                    if topic_comments:
                        for comment in topic_comments[:3]:
                            st.markdown(f"> {comment.text}")

                        if len(topic_comments) > 3:
                            if f"show_more_{i}" not in st.session_state:
                                st.session_state[f"show_more_{i}"] = False

                            if st.button(
                                "Show more comments"
                                if not st.session_state[f"show_more_{i}"]
                                else "Show less comments",
                                key=f"more_comments_{i}",
                            ):
                                st.session_state[f"show_more_{i}"] = not st.session_state[f"show_more_{i}"]

                            if st.session_state[f"show_more_{i}"]:
                                for comment in topic_comments[3:]:
                                    st.markdown(f"> {comment.text}")

            st.subheader("Overall Analysis")
            st.write(comment_analysis.overall_analysis)

        st.button("Start Over", on_click=set_state, args=[0])


if __name__ == "__main__":
    main()
