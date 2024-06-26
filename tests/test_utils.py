from eightify.utils import extract_video_id


def test_extract_youtube_id():
    url = "https://www.youtube.com/watch?v=l-gQLqv9f4o"
    assert extract_video_id(url) == "l-gQLqv9f4o"
