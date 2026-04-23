def parse_feed_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    parsed_entries = []
    for entry in entries:
        content = entry.get("content") or entry.get("description") or ""
        published = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("pubDate")
            or entry.get("created")
            or datetime.now().isoformat()
        )
        entry_id = entry.get("id") or entry.get("link", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        title = entry.get("title", "")
        parsed_entries.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "content": content,
                "published_date": published,
                "entry_id": entry_id,
            }
        )
    return parsed_entries