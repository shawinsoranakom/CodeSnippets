def parse_facebook_post(story_node: Dict[str, Any]) -> Dict[str, Any]:
    try:
        post_info = {
            "post_id": story_node.get("post_id"),
            "story_id": story_node.get("id"),
            "creation_time": None,
            "creation_time_formatted": None,
            "url": None,
        }
        creation_time_sources = [
            story_node.get("creation_time"),
            (story_node.get("comet_sections") or {}).get("context_layout", {}).get("story", {}).get("creation_time"),
            (story_node.get("comet_sections") or {}).get("timestamp", {}).get("story", {}).get("creation_time"),
        ]
        for source in creation_time_sources:
            if source:
                post_info["creation_time"] = source
                post_info["creation_time_formatted"] = datetime.fromtimestamp(source).strftime("%Y-%m-%d %H:%M:%S")
                break
        url_sources = [
            (story_node.get("comet_sections") or {}).get("content", {}).get("story", {}).get("wwwURL"),
            (story_node.get("comet_sections") or {}).get("feedback", {}).get("story", {}).get("story_ufi_container", {}).get("story", {}).get("url"),
            (story_node.get("comet_sections") or {})
            .get("feedback", {})
            .get("story", {})
            .get("story_ufi_container", {})
            .get("story", {})
            .get("shareable_from_perspective_of_feed_ufi", {})
            .get("url"),
            story_node.get("wwwURL"),
            story_node.get("url"),
        ]
        for source in url_sources:
            if source:
                post_info["url"] = source
                break
        message_info = extract_message_content(story_node)
        post_info.update(message_info)
        actors_info = extract_actors_info(story_node)
        post_info.update(actors_info)
        attachments_info = extract_attachments(story_node)
        post_info.update(attachments_info)
        engagement_info = extract_engagement_data(story_node)
        post_info.update(engagement_info)
        privacy_info = extract_privacy_info(story_node)
        post_info.update(privacy_info)
        return post_info
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing post data: {e}")
        return {}