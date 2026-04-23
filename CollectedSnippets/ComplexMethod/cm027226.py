def format_queue(
    queue: SonarrQueue, base_url: str | None = None
) -> dict[str, dict[str, Any]]:
    """Format queue for service response."""
    # Group queue items by download ID to handle season packs
    downloads: dict[str, list[Any]] = {}
    for item in queue.records:
        download_id = getattr(item, "downloadId", None)
        if download_id:
            if download_id not in downloads:
                downloads[download_id] = []
            downloads[download_id].append(item)

    shows = {}
    for items in downloads.values():
        if len(items) == 1:
            # Single episode download
            item = items[0]
            shows[item.title] = format_queue_item(item, base_url)
        else:
            # Multiple episodes (season pack) - use first item for main data
            item = items[0]
            formatted = format_queue_item(item, base_url)

            # Get all episode numbers for this download
            episode_numbers = sorted(
                getattr(i.episode, "episodeNumber", 0)
                for i in items
                if hasattr(i, "episode")
            )

            # Format as season pack
            if episode_numbers:
                min_ep = min(episode_numbers)
                max_ep = max(episode_numbers)
                formatted["is_season_pack"] = True
                formatted["episode_count"] = len(episode_numbers)
                formatted["episode_range"] = f"E{min_ep:02d}-E{max_ep:02d}"
                # Update identifier to show it's a season pack
                if formatted.get("season_number") is not None:
                    formatted["episode_identifier"] = (
                        f"S{formatted['season_number']:02d} "
                        f"({len(episode_numbers)} episodes)"
                    )

            shows[item.title] = formatted

    return shows