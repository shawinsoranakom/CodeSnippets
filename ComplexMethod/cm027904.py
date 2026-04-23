def crawl_pending_entries(tracking_db_path=None, batch_size=20, delay_range=(1, 3), max_attempts=3):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    entries = get_uncrawled_entries(tracking_db_path, limit=batch_size, max_attempts=max_attempts)
    stats = {
        "total_entries": len(entries),
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
    }
    for entry in entries:
        entry_id = entry["id"]
        url = entry["link"]
        if not url or url.strip() == "":
            update_entry_status(tracking_db_path, entry_id, "skipped")
            stats["skipped_count"] += 1
            continue
        print(f"Crawling URL: {url}")
        try:
            web_data = get_web_data(url)
            if not web_data or not web_data["raw_html"]:
                print(f"No content retrieved for {url}")
                update_entry_status(tracking_db_path, entry_id, "failed")
                stats["failed_count"] += 1
                continue
            success = store_crawled_article(tracking_db_path, entry, web_data["raw_html"], web_data["metadata"])
            if success:
                update_entry_status(tracking_db_path, entry_id, "success")
                stats["success_count"] += 1
                print(f"Successfully crawled: {url}")
            else:
                update_entry_status(tracking_db_path, entry_id, "failed")
                stats["failed_count"] += 1
                print(f"Failed to store: {url} (likely duplicate)")
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            update_entry_status(tracking_db_path, entry_id, "failed")
            stats["failed_count"] += 1
    return stats