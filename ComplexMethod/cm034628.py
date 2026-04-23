def to_bytes(image: ImageType) -> bytes:
    """
    Converts the given image to bytes.

    Args:
        image (ImageType): The image to convert.

    Returns:
        bytes: The image as bytes.
    """
    if isinstance(image, bytes):
        return image
    elif isinstance(image, str):
        if image.startswith("data:"):
            is_data_uri_an_image(image)
            return extract_data_uri(image)
        elif image.startswith("http://") or image.startswith("https://"):
            if not is_safe_url(image):
                raise ValueError("Invalid or disallowed media URL")
            path: str = urlparse(image).path
            if path.startswith("/files/"):
                path = get_bucket_dir(*path.split("/")[2:])
                if os.path.exists(path):
                    return Path(path).read_bytes()
                else:
                    raise FileNotFoundError(f"File not found: {path}")
            else:
                resp = requests.get(image, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
                })
                if resp.ok and is_accepted_format(resp.content):
                    return resp.content
                raise ValueError("Invalid image url. Expected bytes, str, or PIL Image.")
        else:
            raise ValueError("Invalid image format. Expected bytes, str, or PIL Image.")
    elif isinstance(image, Image.Image):
        bytes_io = BytesIO()
        image.save(bytes_io, image.format)
        image.seek(0)
        return bytes_io.getvalue()
    elif isinstance(image, os.PathLike):
        return Path(image).read_bytes()
    elif isinstance(image, Path):
        return image.read_bytes()
    else:
        try:
            image.seek(0)
        except (AttributeError, io.UnsupportedOperation):
            pass
        return image.read()