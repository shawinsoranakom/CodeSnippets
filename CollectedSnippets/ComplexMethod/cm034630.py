async def save_response_media(response, prompt: str, tags: list[str] = [], transcript: str = None, content_type: str = None) -> AsyncIterator:
    """Save media from response to local file and return URL"""
    if isinstance(response, dict):
        content_type = response.get("mimeType", content_type or "audio/mpeg")
        transcript = response.get("transcript")
        response = response.get("data")
    elif hasattr(response, "headers"):
        content_type = response.headers.get("content-type", content_type)
    elif not content_type:
        raise ValueError("Response must be a dict or have headers")

    if isinstance(response, str):
        response = base64.b64decode(response)
    extension = MEDIA_TYPE_MAP.get(content_type)
    if extension is None:
        raise ValueError(f"Unsupported media type: {content_type}")

    filename = get_filename(tags, prompt, f".{extension}", prompt)
    if hasattr(response, "headers"):
        filename = update_filename(response, filename)
    target_path = os.path.join(get_media_dir(), filename)
    ensure_media_dir()
    with open(target_path, 'wb') as f:
        if isinstance(response, bytes):
            f.write(response)
        else:
            if hasattr(response, "iter_content"):
                iter_response = response.iter_content()
            else:
                iter_response = response.content.iter_any()
            async for chunk in iter_response:
                f.write(chunk)

    # Base URL without request parameters
    media_url = f"/media/{filename}"

    # Save the original URL in the metadata, but not in the file path itself
    source_url = None
    if hasattr(response, "url") and response.method == "GET":
        source_url = str(response.url)

    if content_type.startswith("audio/"):
        yield AudioResponse(media_url, transcript, source_url=source_url)
    elif content_type.startswith("video/"):
        yield VideoResponse(media_url, prompt, source_url=source_url)
    else:
        yield ImageResponse(media_url, prompt, source_url=source_url)