from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from eightify.api import openai, youtube

load_dotenv()

app = FastAPI()


class VideoRequest(BaseModel):
    video_id: str


class SummarizeResponse(BaseModel):
    summary: str


class CommentAnalysisRequest(BaseModel):
    video_id: str
    insight_request: Optional[str] = None


class CommentAnalysisResponse(BaseModel):
    comment_analysis: str


# TODO: cache video details, transcript, and summary
@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_video(request: VideoRequest):
    video_details = youtube.get_video_details(request.video_id)
    if not video_details:
        raise HTTPException(status_code=404, detail="Video not found")

    transcript = youtube.get_video_transcript(request.video_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not available")

    # TODO: use async APIs
    summary = openai.summarize_text(transcript.text, video_details.title, video_details.description)

    return SummarizeResponse(summary=summary)


@app.post("/analyze_comments", response_model=CommentAnalysisResponse)
async def analyze_video_comments(request: CommentAnalysisRequest):
    comments = youtube.get_video_comments(request.video_id)
    comment_analysis = openai.analyze_comments(comments, request.insight_request)

    return CommentAnalysisResponse(comment_analysis=comment_analysis)


@app.get("/")
async def root():
    return {"message": "Welcome to the YouTube Summarizer API"}
