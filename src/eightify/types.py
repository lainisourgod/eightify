from pydantic import BaseModel


class VideoSummary(BaseModel):
    summary: str
    comment_analysis: str


class VideoFeedback(BaseModel):
    helpful: bool
    feedback: str


class VideoDetails(BaseModel):
    title: str
    description: str


class VideoTranscript(BaseModel):
    text: str


class VideoComment(BaseModel):
    text: str
