def extract_message_content(story_node: Dict[str, Any]) -> Dict[str, Any]:
    message_info = {"message_text": "", "hashtags": [], "mentions": [], "links": []}
    try:
        message_sources = [
            (story_node.get("message") or {}).get("text", ""),
            ((((story_node.get("comet_sections") or {}).get("content") or {}).get("story") or {}).get("message") or {}).get("text", ""),
        ]
        for source in message_sources:
            if source:
                message_info["message_text"] = source
                break
        message_data = story_node.get("message", {})
        if "ranges" in message_data:
            for range_item in message_data["ranges"]:
                entity = range_item.get("entity", {})
                entity_type = entity.get("__typename")

                if entity_type == "Hashtag":
                    hashtag_text = message_info["message_text"][range_item["offset"] : range_item["offset"] + range_item["length"]]
                    message_info["hashtags"].append(
                        {
                            "text": hashtag_text,
                            "url": entity.get("url"),
                            "id": entity.get("id"),
                        }
                    )
                elif entity_type == "User":
                    mention_text = message_info["message_text"][range_item["offset"] : range_item["offset"] + range_item["length"]]
                    message_info["mentions"].append(
                        {
                            "text": mention_text,
                            "url": entity.get("url"),
                            "id": entity.get("id"),
                        }
                    )
    except (KeyError, TypeError):
        pass
    return message_info