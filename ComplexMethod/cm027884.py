def format_media(fb_post_data: Dict[str, Any]) -> str:
    media_items = []
    photos = fb_post_data.get("photos", [])
    for photo in photos:
        if isinstance(photo, dict):
            media_item = {
                "type": "image",
                "url": photo.get("image_uri") or photo.get("url", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "id": photo.get("id"),
                "accessibility_caption": photo.get("accessibility_caption", ""),
            }
            media_item = {k: v for k, v in media_item.items() if v is not None}
            media_items.append(media_item)

    videos = fb_post_data.get("videos", [])
    for video in videos:
        if isinstance(video, dict):
            media_item = {
                "type": "video",
                "url": video.get("url", ""),
                "id": video.get("id"),
            }
            media_item = {k: v for k, v in media_item.items() if v is not None}
            media_items.append(media_item)

    attachments = fb_post_data.get("attachments", [])
    for attachment in attachments:
        if isinstance(attachment, dict):
            attachment_type = attachment.get("type", "")
            style_list = attachment.get("style_list", [])
            if "photo" in style_list:
                media_item = {"type": "image", "attachment_type": attachment_type}
                media_items.append(media_item)
            elif "video" in style_list:
                media_item = {"type": "video", "attachment_type": attachment_type}
                media_items.append(media_item)
    return media_items or []