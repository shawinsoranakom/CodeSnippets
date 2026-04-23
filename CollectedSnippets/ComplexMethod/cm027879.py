def extract_actors_info(story_node: Dict[str, Any]) -> Dict[str, Any]:
    actors_info = {
        "author_name": "",
        "author_id": "",
        "author_url": "",
        "author_profile_picture": "",
        "is_verified": False,
        "page_info": {},
    }
    try:
        actors = story_node.get("actors", [])
        if actors:
            main_actor = actors[0]
            actors_info.update(
                {
                    "author_name": main_actor.get("name", ""),
                    "author_id": main_actor.get("id", ""),
                    "author_url": main_actor.get("url", ""),
                }
            )
        context_sections = (story_node.get("comet_sections") or {}).get("context_layout", {})
        if context_sections:
            actor_photo = (context_sections.get("story") or {}).get("comet_sections", {}).get("actor_photo", {})
            if actor_photo:
                story_actors = (actor_photo.get("story") or {}).get("actors", [])
                if story_actors:
                    profile_pic = story_actors[0].get("profile_picture", {})
                    actors_info["author_profile_picture"] = profile_pic.get("uri", "")
    except (KeyError, TypeError, IndexError):
        pass
    return actors_info