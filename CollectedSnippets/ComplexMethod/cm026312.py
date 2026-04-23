def format_queue_item(item: Any, base_url: str | None = None) -> dict[str, Any]:
    """Format a single queue item."""

    remaining = 1 if item.size == 0 else item.sizeleft / item.size
    remaining_pct = 100 * (1 - remaining)

    movie = item.movie

    result: dict[str, Any] = {
        "id": item.id,
        "movie_id": item.movieId,
        "title": movie["title"],
        "download_title": item.title,
        "progress": f"{remaining_pct:.2f}%",
        "size": item.size,
        "size_left": item.sizeleft,
        "status": item.status,
        "tracked_download_status": getattr(item, "trackedDownloadStatus", None),
        "tracked_download_state": getattr(item, "trackedDownloadState", None),
        "download_client": getattr(item, "downloadClient", None),
        "download_id": getattr(item, "downloadId", None),
        "indexer": getattr(item, "indexer", None),
        "protocol": str(getattr(item, "protocol", None)),
        "estimated_completion_time": str(
            getattr(item, "estimatedCompletionTime", None)
        ),
        "time_left": str(getattr(item, "timeleft", None)),
    }

    if quality := getattr(item, "quality", None):
        result["quality"] = quality.quality.name

    if languages := getattr(item, "languages", None):
        result["languages"] = [lang.name for lang in languages]

    if custom_format_score := getattr(item, "customFormatScore", None):
        result["custom_format_score"] = custom_format_score

    # Add movie images if available
    # Note: item.movie is a dict (not object), so images are also dicts
    if images := movie.get("images"):
        result["images"] = {}
        for image in images:
            cover_type = image.get("coverType")
            # Prefer remoteUrl (public TMDB URL) over local path
            if remote_url := image.get("remoteUrl"):
                result["images"][cover_type] = remote_url
            elif base_url and (url := image.get("url")):
                result["images"][cover_type] = f"{base_url.rstrip('/')}{url}"

    return result