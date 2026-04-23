def merge_media(media: list, messages: list) -> Iterator:
    buffer = []
    # Read media from the last user message
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, list):
                for part in content:
                    if "type" not in part and "name" in part and "text" not in part:
                        path = render_media(**part, as_path=True)
                        buffer.append((path, os.path.basename(path)))
                    elif part.get("type") == "image_url":
                        path: str = urlparse(part.get("image_url")).path
                        if path.startswith("/files/"):
                            path = get_bucket_dir(path.split(path, "/")[1:])
                            if os.path.exists(path):
                                buffer.append((Path(path), os.path.basename(path)))
                            else:
                                buffer.append((part.get("image_url"), None))
                        else:
                            buffer.append((part.get("image_url"), None))
        else:
            buffer = []
    yield from buffer
    if media is not None:
        yield from media