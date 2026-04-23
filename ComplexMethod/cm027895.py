def _add_source_names(cursor, articles):
    source_ids = {a.get("source_id") for a in articles if a.get("source_id")}
    feed_ids = {a.get("feed_id") for a in articles if a.get("feed_id")}
    if not source_ids and not feed_ids:
        return
    source_names = {}
    if source_ids:
        source_ids = [id for id in source_ids if id is not None]
        if source_ids:
            placeholders = ",".join(["?"] * len(source_ids))
            try:
                cursor.execute(
                    f"SELECT id, name FROM sources WHERE id IN ({placeholders})",
                    list(source_ids),
                )
                for row in cursor.fetchall():
                    source_names[row["id"]] = row["name"]
            except Exception as e:
                print(f"Error fetching source names: {e}")
    if feed_ids:
        feed_ids = [id for id in feed_ids if id is not None]
        if feed_ids:
            placeholders = ",".join(["?"] * len(feed_ids))
            try:
                cursor.execute(
                    f"""
                    SELECT sf.id, s.name 
                    FROM source_feeds sf
                    JOIN sources s ON sf.source_id = s.id
                    WHERE sf.id IN ({placeholders})
                """,
                    list(feed_ids),
                )
                for row in cursor.fetchall():
                    source_names[row["id"]] = row["name"]
            except Exception as e:
                print(f"Error fetching feed source names: {e}")
    for article in articles:
        source_id = article.get("source_id")
        feed_id = article.get("feed_id")
        if source_id and source_id in source_names:
            article["source_name"] = source_names[source_id]
        elif feed_id and feed_id in source_names:
            article["source_name"] = source_names[feed_id]
        else:
            article["source_name"] = "Unknown Source"