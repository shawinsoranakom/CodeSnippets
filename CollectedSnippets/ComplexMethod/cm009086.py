def _url_to_size(image_source: str) -> tuple[int, int] | None:
    try:
        from PIL import Image  # type: ignore[import]
    except ImportError:
        logger.info(
            "Unable to count image tokens. To count image tokens please install "
            "`pip install -U pillow httpx`."
        )
        return None
    if _is_url(image_source):
        import httpx

        # Set reasonable limits to prevent resource exhaustion
        # Timeout prevents indefinite hangs on slow/malicious servers
        timeout = 5.0  # seconds
        # Max size matches OpenAI's 50 MB payload limit
        max_size = 50 * 1024 * 1024  # 50 MB

        try:
            response = _get_ssrf_safe_client().get(image_source, timeout=timeout)
            response.raise_for_status()

            # Check response size before loading into memory
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > max_size:
                logger.warning(
                    "Image URL exceeds maximum size limit of %d bytes", max_size
                )
                return None

            # Also check actual content size
            if len(response.content) > max_size:
                logger.warning(
                    "Image URL exceeds maximum size limit of %d bytes", max_size
                )
                return None

            with Image.open(BytesIO(response.content)) as img:
                width, height = img.size
            return width, height
        except httpx.TimeoutException:
            logger.warning("Image URL request timed out after %s seconds", timeout)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("Image URL returned HTTP error: %s", e)
            return None
        except Exception as e:
            logger.warning("Failed to fetch or process image from URL: %s", e)
            return None

    if _is_b64(image_source):
        _, encoded = image_source.split(",", 1)
        data = base64.b64decode(encoded)
        with Image.open(BytesIO(data)) as img:
            width, height = img.size
        return width, height
    return None