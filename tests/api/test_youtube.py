from eightify.api.youtube import get_video_details, get_video_transcript, get_video_comments

TEST_VIDEO_ID = "dQw4w9WgXcQ"


def test_integration_get_video_details():
    result = get_video_details(TEST_VIDEO_ID)
    assert isinstance(result, dict)
    assert "title" in result and result["title"]
    assert "description" in result and result["description"]
    assert "Never Gonna Give You Up" in result["title"]
    assert "Never Gonna Give You Up" in result["description"]


def test_integration_get_video_transcript():
    result = get_video_transcript(TEST_VIDEO_ID)
    assert result
    assert isinstance(result, str)
    assert "never going to sing goodbye" in result


def test_integration_get_video_comments():
    result = get_video_comments(TEST_VIDEO_ID)
    assert result
    assert isinstance(result, list)
    assert len(result) > 0  # Ensure we got at least one comment
    assert isinstance(result[0], str)  # Check that comments are strings
