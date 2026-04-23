def extract_bucket_items(messages: Messages) -> list[dict]:
    """Extract bucket items from messages content."""
    bucket_items = []
    for message in messages:
        if isinstance(message, dict) and isinstance(message.get("content"), list):
            for content_item in message["content"]:
                if isinstance(content_item, dict) and "bucket_id" in content_item and "name" not in content_item:
                    bucket_items.append(content_item)
        if message.get("role") == "assistant":
            bucket_items = []
    return bucket_items