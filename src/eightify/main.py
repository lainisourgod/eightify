from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from eightify.api import youtube, openai
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoRequest(BaseModel):
    video_id: str
    insight_request: Optional[str] = None


@app.post("/summarize")
async def summarize_video(request: VideoRequest):
    video_details = youtube.get_video_details(request.video_id)
    if not video_details:
        raise HTTPException(status_code=404, detail="Video not found")

    transcript = youtube.get_video_transcript(request.video_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not available")

    summary = openai.summarize_text(
        transcript, video_details["title"], video_details["description"]
    )

    comments = youtube.get_video_comments(request.video_id)
    comment_analysis = openai.analyze_comments(comments, request.insight_request)

    return {
        "video_details": video_details,
        "summary": summary,
        "comment_analysis": comment_analysis,
    }


@app.get("/")
async def root():
    return {"message": "Welcome to the YouTube Summarizer API"}
