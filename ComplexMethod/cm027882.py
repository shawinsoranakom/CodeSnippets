def extract_privacy_info(story_node: Dict[str, Any]) -> Dict[str, Any]:
    privacy_info = {"privacy_scope": "", "audience": ""}
    try:
        privacy_sources = [
            (story_node.get("comet_sections") or {}).get("context_layout", {}).get("story", {}).get("privacy_scope", {}),
            story_node.get("privacy_scope", {}),
            next(
                (
                    (meta.get("story") or {}).get("privacy_scope", {})
                    for meta in (story_node.get("comet_sections") or {})
                    .get("context_layout", {})
                    .get("story", {})
                    .get("comet_sections", {})
                    .get("metadata", [])
                    if isinstance(meta, dict) and meta.get("__typename") == "CometFeedStoryAudienceStrategy"
                ),
                {},
            ),
        ]
        for privacy_scope in privacy_sources:
            if privacy_scope and "description" in privacy_scope:
                privacy_info["privacy_scope"] = privacy_scope["description"]
                break
        if not privacy_info["privacy_scope"]:
            context_layout = (story_node.get("comet_sections") or {}).get("context_layout", {})
            if context_layout:
                story = context_layout.get("story", {})
                comet_sections = story.get("comet_sections", {})
                metadata = comet_sections.get("metadata", [])
                for meta_item in metadata:
                    if isinstance(meta_item, dict) and meta_item.get("__typename") == "CometFeedStoryAudienceStrategy":
                        story_data = meta_item.get("story", {})
                        privacy_scope = story_data.get("privacy_scope", {})
                        if privacy_scope:
                            privacy_info["privacy_scope"] = privacy_scope.get("description", "")
                            break
    except (KeyError, TypeError):
        pass
    return privacy_info