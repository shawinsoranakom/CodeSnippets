def process_post_data(post_data):
    data = post_data.copy()
    metrics = ["engagement_reply_count", "engagement_retweet_count", "engagement_like_count", "engagement_bookmark_count", "engagement_view_count"]
    for metric in metrics:
        if metric in data:
            data[metric] = parse_engagement_count(data[metric])
    if "media" in data and isinstance(data["media"], list):
        data["media"] = json.dumps(data["media"])
    if "categories" in data and isinstance(data["categories"], list):
        data["categories"] = json.dumps(data["categories"])
    if "tags" in data and isinstance(data["tags"], list):
        data["tags"] = json.dumps(data["tags"])
    if "is_ad" in data:
        data["is_ad"] = 1 if data["is_ad"] else 0
    return data