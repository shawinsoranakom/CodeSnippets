def fetch_cover_images(page: str = "", item: str = "", index: int = 0):
    from starlette.responses import Response

    page = next(iter([x for x in extra_pages if x.name == page]), None)
    if page is None:
        raise HTTPException(status_code=404, detail="File not found")

    metadata = page.metadata.get(item)
    if metadata is None:
        raise HTTPException(status_code=404, detail="File not found")

    cover_images = json.loads(metadata.get('ssmd_cover_images', {}))
    image = cover_images[index] if index < len(cover_images) else None
    if not image:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        image = Image.open(BytesIO(b64decode(image)))
        buffer = BytesIO()
        image.save(buffer, format=image.format)
        return Response(content=buffer.getvalue(), media_type=image.get_format_mimetype())
    except Exception as err:
        raise ValueError(f"File cannot be fetched: {item}. Failed to load cover image.") from err