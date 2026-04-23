def extract_engagement_data(story_node: Dict[str, Any]) -> Dict[str, Any]:
    """Extract likes, comments, shares, and other engagement metrics"""
    engagement_info = {
        "reaction_count": 0,
        "comment_count": 0,
        "share_count": 0,
        "reactions_breakdown": {},
        "top_reactions": [],
    }
    try:
        feedback_story = (story_node.get("comet_sections") or {}).get("feedback", {}).get("story", {})
        if feedback_story:
            ufi_container = (feedback_story.get("story_ufi_container") or {}).get("story", {})
            if ufi_container:
                feedback_context = ufi_container.get("feedback_context", {})
                feedback_target = feedback_context.get("feedback_target_with_context", {})

                if feedback_target:
                    summary_renderer = feedback_target.get("comet_ufi_summary_and_actions_renderer", {})
                    if summary_renderer:
                        feedback_data = summary_renderer.get("feedback", {})
                        if "i18n_reaction_count" in feedback_data:
                            engagement_info["reaction_count"] = int(feedback_data["i18n_reaction_count"])
                        elif "reaction_count" in feedback_data and isinstance(feedback_data["reaction_count"], dict):
                            engagement_info["reaction_count"] = feedback_data["reaction_count"].get("count", 0)
                        if "i18n_share_count" in feedback_data:
                            engagement_info["share_count"] = int(feedback_data["i18n_share_count"])
                        elif "share_count" in feedback_data and isinstance(feedback_data["share_count"], dict):
                            engagement_info["share_count"] = feedback_data["share_count"].get("count", 0)
                        top_reactions = feedback_data.get("top_reactions", {})
                        if "edges" in top_reactions:
                            for edge in top_reactions["edges"]:
                                reaction_node = edge.get("node", {})
                                engagement_info["top_reactions"].append(
                                    {
                                        "reaction_id": reaction_node.get("id"),
                                        "name": reaction_node.get("localized_name"),
                                        "count": edge.get("reaction_count", 0),
                                    }
                                )
                    comment_rendering = feedback_target.get("comment_rendering_instance", {})
                    if comment_rendering:
                        comments = comment_rendering.get("comments", {})
                        engagement_info["comment_count"] = comments.get("total_count", 0)

    except (KeyError, TypeError, ValueError):
        pass
    return engagement_info