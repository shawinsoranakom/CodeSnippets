async def send_final_presentation_blocks(thread_key: str, state_data: dict, response_text: str):
    script = state_data.get("generated_script", {})
    podcast_title = script.get("title") if isinstance(script, dict) else None
    if not podcast_title:
        podcast_title = state_data.get("podcast_info", {}).get("topic", "Your Podcast")
    audio_url = state_data.get("audio_url")
    banner_url = state_data.get("banner_url")
    banner_images = state_data.get("banner_images", [])
    full_audio_url = f"{API_BASE_URL}/audio/{audio_url}" if audio_url else None
    full_banner_url = None
    if banner_images:
        full_banner_url = f"{API_BASE_URL}/podcast_img/{banner_images[0]}"
    elif banner_url:
        full_banner_url = f"{API_BASE_URL}/podcast_img/{banner_url}"
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🎉 Podcast Complete!*\n{response_text}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{podcast_title}*\n\nYour podcast has been successfully created with all assets! 🎊",
            },
        },
    ]
    if full_banner_url:
        blocks.append(
            {
                "type": "image",
                "image_url": full_banner_url,
                "alt_text": f"Banner for {podcast_title}",
            }
        )
    action_elements = []
    if full_audio_url:
        action_elements.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🎵 Download Audio"},
                "url": full_audio_url,
                "action_id": "download_final_audio",
            }
        )
    action_elements.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "🎙️ Create New Podcast"},
            "style": "primary",
            "action_id": "new_podcast",
            "value": thread_key,
        }
    )
    blocks.append({"type": "actions", "elements": action_elements})
    await send_slack_blocks(thread_key, blocks, "🎉 Podcast Complete!")