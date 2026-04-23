async def get_file_extension(response: ClientResponse):
    """
    Attempts to determine the file extension from an aiohttp response.  Improved to handle more types.

    Args:
        response: The aiohttp ClientResponse object.

    Returns:
        The file extension (e.g., ".html", ".json", ".pdf", ".zip", ".md", ".txt") as a string,
        or None if it cannot be determined.
    """

    content_type = response.headers.get('Content-Type')
    if content_type:
        if "html" in content_type.lower():
            return ".html"
        elif "json" in content_type.lower():
            return ".json"
        elif "pdf" in content_type.lower():
            return ".pdf"
        elif "zip" in content_type.lower():
            return ".zip"
        elif "text/plain" in content_type.lower():
            return ".txt"
        elif "markdown" in content_type.lower():
            return ".md"

    url = str(response.url)
    if url:
        return Path(url).suffix.lower()

    return None