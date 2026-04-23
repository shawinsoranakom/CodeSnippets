def format_queue_item(item: Any, base_url: str | None = None) -> dict[str, Any]:
    """Format a single queue item."""
    # Calculate progress
    remaining = 1 if item.size == 0 else item.sizeleft / item.size
    remaining_pct = 100 * (1 - remaining)

    result: dict[str, Any] = {
        "id": item.id,
        "series_id": getattr(item, "seriesId", None),
        "episode_id": getattr(item, "episodeId", None),
        "title": item.series.title,
        "download_title": item.title,
        "season_number": getattr(item, "seasonNumber", None),
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
        "episode_has_file": getattr(item, "episodeHasFile", None),
        "estimated_completion_time": str(
            getattr(item, "estimatedCompletionTime", None)
        ),
        "time_left": str(getattr(item, "timeleft", None)),
    }

    # Add episode information from the episode object if available
    if episode := getattr(item, "episode", None):
        result["episode_number"] = getattr(episode, "episodeNumber", None)
        result["episode_title"] = getattr(episode, "title", None)
        # Add formatted identifier like the sensor uses (if we have both season and episode)
        if result["season_number"] is not None and result["episode_number"] is not None:
            result["episode_identifier"] = (
                f"S{result['season_number']:02d}E{result['episode_number']:02d}"
            )

    # Add quality information if available
    if quality := getattr(item, "quality", None):
        result["quality"] = quality.quality.name

    # Add language information if available
    if languages := getattr(item, "languages", None):
        result["languages"] = [lang["name"] for lang in languages]

    # Add custom format score if available
    if custom_format_score := getattr(item, "customFormatScore", None):
        result["custom_format_score"] = custom_format_score

    # Add series images if available
    if images := getattr(item.series, "images", None):
        result["images"] = {}
        for image in images:
            cover_type = image.coverType
            # Prefer remoteUrl (public TVDB URL) over local path
            if remote_url := getattr(image, "remoteUrl", None):
                result["images"][cover_type] = remote_url
            elif base_url and (url := getattr(image, "url", None)):
                result["images"][cover_type] = f"{base_url.rstrip('/')}{url}"

    return result