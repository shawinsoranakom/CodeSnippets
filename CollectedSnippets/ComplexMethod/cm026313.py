def format_movie_item(
    movie: RadarrMovie, base_url: str | None = None
) -> dict[str, Any]:
    """Format a single movie item."""
    result: dict[str, Any] = {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "tmdb_id": movie.tmdbId,
        "imdb_id": getattr(movie, "imdbId", None),
        "status": movie.status,
        "monitored": movie.monitored,
        "has_file": movie.hasFile,
        "size_on_disk": getattr(movie, "sizeOnDisk", None),
    }

    # Add path if available
    if path := getattr(movie, "path", None):
        result["path"] = path

    # Add movie statistics if available
    if statistics := getattr(movie, "statistics", None):
        result["movie_file_count"] = getattr(statistics, "movieFileCount", None)
        result["size_on_disk"] = getattr(statistics, "sizeOnDisk", None)

    # Add movie images if available
    if images := getattr(movie, "images", None):
        images_dict: dict[str, str] = {}
        for image in images:
            cover_type = image.coverType
            # Prefer remoteUrl (public TMDB URL) over local path
            if remote_url := getattr(image, "remoteUrl", None):
                images_dict[cover_type] = remote_url
            elif base_url and (url := getattr(image, "url", None)):
                images_dict[cover_type] = f"{base_url.rstrip('/')}{url}"
        result["images"] = images_dict

    return result