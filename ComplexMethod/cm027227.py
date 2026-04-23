def format_series(
    series_list: list[SonarrSeries], base_url: str | None = None
) -> dict[str, dict[str, Any]]:
    """Format series list for service response."""
    formatted_shows = {}

    for series in series_list:
        series_title = series.title
        formatted_shows[series_title] = {
            "id": series.id,
            "year": series.year,
            "tvdb_id": getattr(series, "tvdbId", None),
            "imdb_id": getattr(series, "imdbId", None),
            "status": series.status,
            "monitored": series.monitored,
        }

        # Add episode statistics if available (like the sensor shows)
        if statistics := getattr(series, "statistics", None):
            episode_file_count = getattr(statistics, "episodeFileCount", None)
            episode_count = getattr(statistics, "episodeCount", None)
            formatted_shows[series_title]["episode_file_count"] = episode_file_count
            formatted_shows[series_title]["episode_count"] = episode_count
            # Only format episodes_info if we have valid data
            if episode_file_count is not None and episode_count is not None:
                formatted_shows[series_title]["episodes_info"] = (
                    f"{episode_file_count}/{episode_count} Episodes"
                )
            else:
                formatted_shows[series_title]["episodes_info"] = None

        # Add series images if available
        if images := getattr(series, "images", None):
            images_dict: dict[str, str] = {}
            for image in images:
                cover_type = image.coverType
                # Prefer remoteUrl (public TVDB URL) over local path
                if remote_url := getattr(image, "remoteUrl", None):
                    images_dict[cover_type] = remote_url
                elif base_url and (url := getattr(image, "url", None)):
                    images_dict[cover_type] = f"{base_url.rstrip('/')}{url}"
            formatted_shows[series_title]["images"] = images_dict

    return formatted_shows