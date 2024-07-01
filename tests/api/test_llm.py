import pytest

from eightify.api.llm import analyze_and_cluster_comments, summarize_text
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

    assert summary is not None
    assert len(summary) > 0
    assert "AI" in summary or "artificial intelligence" in summary.lower()


from eightify.api.llm import analyze_and_cluster_comments, summarize_text
from eightify.common import CommentAnalysis, CommentTopic, VideoComment, VideoDetails


@pytest.mark.integration
def test_analyze_comments():
    comments = [
        "Great video! I learned a lot about AI.",
        "I'm concerned about the ethical implications of AI. Can you make a video about that?",
        "This content is so informative. Keep up the good work!",
        "I disagree with some points. AI isn't as advanced as you claim.",
        "Nice background music!",  # This comment might be filtered out as uninteresting
    ]

    analysis = analyze_and_cluster_comments(
        [VideoComment(text=comment) for comment in comments],
        VideoDetails(
            title="The Impact of AI on Society",
            description="Exploring the benefits and challenges of artificial intelligence.",
        ),
    )

    assert isinstance(analysis, CommentAnalysis)
    assert len(analysis.overall_analysis) > 0
    assert "AI" in analysis.overall_analysis or "artificial intelligence" in analysis.overall_analysis.lower()
    assert len(analysis.topics) > 0
    assert len(analysis.comments) == len(comments)  # All original comments are preserved

    # Check if all topics have at least one comment
    assert all(len(topic.comment_indices) > 0 for topic in analysis.topics)

    # Check if some comments might not be assigned to any topic (filtered out as uninteresting)
    assigned_comment_indices = set()
    for topic in analysis.topics:
        assigned_comment_indices.update(topic.comment_indices)
    assert len(assigned_comment_indices) <= len(comments)

    # Check if the overall analysis mentions key aspects from the video details
    assert "society" in analysis.overall_analysis.lower() or "impact" in analysis.overall_analysis.lower()


@pytest.mark.integration
def test_analyze_comments_with_insight_request():
    comments = [
        "The explanation of machine learning algorithms was excellent!",
        "Could you cover more about deep learning in your next video?",
        "I'm a beginner, and this helped me understand AI basics.",
        "As a data scientist, I appreciate the technical depth of your content.",
        "The intro music was too loud.",  # This comment might be filtered out as uninteresting
    ]
    insight_request = "Analyze the technical level of understanding among the viewers."

    analysis = analyze_and_cluster_comments(
        [VideoComment(text=comment) for comment in comments],
        VideoDetails(
            title="The Impact of AI on Society",
            description="Exploring the benefits and challenges of artificial intelligence.",
        ),
        insight_request=insight_request,
    )

    assert isinstance(analysis, CommentAnalysis)
    assert len(analysis.overall_analysis) > 0
    assert "technical" in analysis.overall_analysis.lower()
    assert "understanding" in analysis.overall_analysis.lower() or "knowledge" in analysis.overall_analysis.lower()
    assert len(analysis.topics) > 0
    assert len(analysis.comments) == len(comments)  # All original comments are preserved

    # Check if the insight request is addressed in the analysis
    assert any(word in analysis.overall_analysis.lower() for word in ["beginner", "data scientist", "technical level"])

    # Check if topics reflect different levels of understanding
    topic_names = [topic.name.lower() for topic in analysis.topics]
    assert any("beginner" in name or "basic" in name for name in topic_names)
    assert any("advanced" in name or "technical" in name for name in topic_names)

    # Verify that relevant comments are assigned to appropriate topics
    for topic in analysis.topics:
        if "beginner" in topic.name.lower() or "basic" in topic.name.lower():
            assert any("beginner" in analysis.comments[i].text.lower() for i in topic.comment_indices)
        if "advanced" in topic.name.lower() or "technical" in topic.name.lower():
            assert any("data scientist" in analysis.comments[i].text.lower() for i in topic.comment_indices)

    # Check if some comments might not be assigned to any topic (filtered out as uninteresting)
    assigned_comment_indices = set()
    for topic in analysis.topics:
        assigned_comment_indices.update(topic.comment_indices)
    assert len(assigned_comment_indices) <= len(comments)
