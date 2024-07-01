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
    points: list[str]


class VideoComment(BaseModel):
    text: str


class CommentTopic(BaseModel):
    name: str
    description: str
    comment_indices: list[int]


class CommentAnalysis(BaseModel):
    comments: list[VideoComment]
    overall_analysis: str
    topics: list[CommentTopic]
