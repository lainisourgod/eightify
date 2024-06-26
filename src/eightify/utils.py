import re


def extract_video_id(url: str) -> str | None:
    """
    Extracts the YouTube video ID from a given URL.
    Based on this: https://stackoverflow.com/a/51870158. Good explanation inside.
    Why doesn't youtube python api provide a simpler way for this, I don't know.

    Args:
        url (str): The YouTube URL.

    Returns:
        str: The extracted YouTube video ID.
    """
    pattern = re.compile(
        r"(https?:\/\/)?(((m|www)\.)?(youtube(-nocookie)?|youtube.googleapis)\.com.*(v\/|v=|vi=|vi\/|e\/|embed\/|user\/.*\/u\/\d+\/)|youtu\.be\/)([_0-9a-z-]+)",
        re.IGNORECASE,
    )
    match = pattern.match(url)
    if match:
        return match.group(8)
    return None
