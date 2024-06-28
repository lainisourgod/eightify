import pytest

from eightify.api.llm import analyze_comments, summarize_text
from eightify.common import VideoComment, VideoDetails, VideoTranscript


@pytest.mark.integration
def test_summarize_text():
    points = [
        "This is a sample transcript of a video about artificial intelligence.",
        "AI is revolutionizing various industries and has the potential to solve complex problems.",
        "However, it also raises ethical concerns that need to be addressed.",
    ]
    text = "\n".join(points)
    video_title = "The Impact of AI on Society"
    video_description = "Exploring the benefits and challenges of artificial intelligence."

    summary = summarize_text(
        VideoTranscript(text=text, points=points),
        video_title=video_title,
        video_description=video_description,
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    # Sanity check
    assert "AI" in summary or "artificial intelligence" in summary.lower()


@pytest.mark.integration
def test_analyze_comments():
    comments = [
        "Great video! I learned a lot about AI.",
        "I'm concerned about the ethical implications of AI. Can you make a video about that?",
        "This content is so informative. Keep up the good work!",
        "I disagree with some points. AI isn't as advanced as you claim.",
    ]

    analysis = analyze_comments(
        [VideoComment(text=comment) for comment in comments],
        VideoDetails(
            title="The Impact of AI on Society",
            description="Exploring the benefits and challenges of artificial intelligence.",
        ),
    )

    assert isinstance(analysis, str)
    assert len(analysis) > 0
    assert "AI" in analysis or "artificial intelligence" in analysis.lower()


@pytest.mark.integration
def test_analyze_comments_with_insight_request():
    comments = [
        "The explanation of machine learning algorithms was excellent!",
        "Could you cover more about deep learning in your next video?",
        "I'm a beginner, and this helped me understand AI basics.",
        "As a data scientist, I appreciate the technical depth of your content.",
    ]
    insight_request = "Analyze the technical level of understanding among the viewers."

    analysis = analyze_comments(
        [VideoComment(text=comment) for comment in comments],
        VideoDetails(
            title="The Impact of AI on Society",
            description="Exploring the benefits and challenges of artificial intelligence.",
        ),
        insight_request,
    )

    assert isinstance(analysis, str)
    assert len(analysis) > 0
    assert "technical" in analysis.lower()
    assert "understanding" in analysis.lower() or "knowledge" in analysis.lower()
