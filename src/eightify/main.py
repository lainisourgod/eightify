from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.datastructures import State
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from eightify.api import llm, youtube
from eightify.common import CommentAnalysis, VideoDetails, VideoTranscript
from eightify.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the video_summaries, video_details, and transcripts in the app state
    app.state.video_summaries = defaultdict(str)
    app.state.video_details = {}
    app.state.transcripts = {}
    yield
    # Clean up resources if needed
    app.state.video_summaries.clear()
    app.state.video_details.clear()
    app.state.transcripts.clear()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class VideoRequest(BaseModel):
    video_id: str


class SummarizeResponse(BaseModel):
    summary: str


class CommentAnalysisRequest(BaseModel):
    video_id: str
    insight_request: Optional[str] = None


class CommentAnalysisResponse(BaseModel):
    comment_analysis: CommentAnalysis


async def fetch_data(video_id: str, app_state: State, data_type: str, fetch_function) -> VideoDetails | VideoTranscript:
    data_state = getattr(app_state, data_type)

    if video_id not in data_state:
        data = fetch_function(video_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"{data_type.replace('_', ' ').capitalize()} not found")
        data_state[video_id] = data

    return data_state[video_id]


async def fetch_video_details(video_id: str, app_state: State) -> VideoDetails:
    return await fetch_data(video_id, app_state, "video_details", youtube.get_video_details)


async def fetch_video_transcript(video_id: str, app_state: State) -> VideoTranscript:
    return await fetch_data(video_id, app_state, "transcripts", youtube.get_video_transcript)


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_video(request: VideoRequest, fastapi_request: Request):
    video_id = request.video_id
    app_state = fastapi_request.app.state

    video_details = await fetch_video_details(video_id, app_state)
    transcript = await fetch_video_transcript(video_id, app_state)

    # TODO: use async APIs
    summary = llm.summarize_text(
        transcript=transcript,
        video_title=video_details.title,
        video_description=video_details.description,
    )
    if summary is None:
        raise HTTPException(status_code=500, detail="LLM api failed to generate a summary")

    # Store the summary in FastAPI state
    app_state.video_summaries[video_id] = summary

    return SummarizeResponse(summary=summary)


@app.post("/analyze_comments", response_model=CommentAnalysis)
async def analyze_video_comments(request: CommentAnalysisRequest, fastapi_request: Request):
    video_id = request.video_id
    app_state = fastapi_request.app.state
    try:
        video_summary = app_state.video_summaries.get(video_id)
        video_details = await fetch_video_details(video_id, app_state)
    except KeyError:
        raise HTTPException(status_code=404, detail="analyze_comments should be called after summarize_video")

    comments = youtube.get_video_comments(video_id)
    if len(comments) == 0:
        raise HTTPException(status_code=204, detail="No comments found")

    analysis_result = llm.analyze_and_cluster_comments(
        comments=comments,
        video_details=video_details,
        summary=video_summary,
        insight_request=request.insight_request,
    )
    if analysis_result is None:
        raise HTTPException(status_code=500, detail="LLM api failed to generate a comment analysis")

    return analysis_result


@app.get("/")
async def root():
    return {"message": "Welcome to Eightify API — a tool for generating insights from YouTube videos."}


if __name__ == "__main__":
    import uvicorn

    from eightify.config import config

    logger.info(f"Starting with config")
    logger.info(config)

    uvicorn.run("eightify.main:app", host="0.0.0.0", port=8000, reload=True, log_level=config.log_level.lower())
