def contains_facebook_posts(json_obj):
    if not isinstance(json_obj, dict):
        return False
    try:
        data = json_obj.get("data", {})
        viewer = data.get("viewer", {})
        news_feed = viewer.get("news_feed", {})
        edges = news_feed.get("edges", [])

        if isinstance(edges, list) and len(edges) > 0:
            for edge in edges:
                if isinstance(edge, dict) and "node" in edge:
                    node = edge["node"]
                    if isinstance(node, dict) and node.get("__typename") == "Story":
                        return True
        return False
    except (KeyError, TypeError, AttributeError):
        return False