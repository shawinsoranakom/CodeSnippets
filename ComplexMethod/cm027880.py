def extract_attachments(story_node: Dict[str, Any]) -> Dict[str, Any]:
    attachments_info = {"attachments": [], "photos": [], "videos": [], "links": []}
    try:
        attachments = story_node.get("attachments", [])
        for attachment in attachments:
            attachment_data = {
                "type": attachment.get("__typename", ""),
                "style_list": attachment.get("style_list", []),
            }
            if "photo" in attachment.get("style_list", []):
                target = attachment.get("target", {})
                if target.get("__typename") == "Photo":
                    styles = attachment.get("styles", {})
                    if styles:
                        media = (styles.get("attachment") or {}).get("media", {})
                        photo_info = {
                            "id": target.get("id"),
                            "url": media.get("url", ""),
                            "width": (media.get("viewer_image") or {}).get("width"),
                            "height": (media.get("viewer_image") or {}).get("height"),
                            "image_uri": "",
                            "accessibility_caption": media.get("accessibility_caption", ""),
                        }
                        resolution_renderer = media.get("comet_photo_attachment_resolution_renderer", {})
                        if resolution_renderer:
                            image = resolution_renderer.get("image", {})
                            photo_info["image_uri"] = image.get("uri", "")

                        attachments_info["photos"].append(photo_info)
            attachments_info["attachments"].append(attachment_data)
    except (KeyError, TypeError):
        pass
    return attachments_info