async def send_source_selection_blocks(thread_key: str, state_data: dict, response_text: str):
    sources = state_data.get("search_results", [])
    languages = state_data.get("available_languages", [{"code": "en", "name": "English"}])
    session_info = get_session_info(thread_key)
    if session_info:
        save_session_state(session_info[0], state_data)
    source_options = []
    for i, source in enumerate(sources[:10]):
        title = source.get("title", f"Source {i + 1}")
        if len(title) > 70:
            title = title[:67] + "..."
        source_options.append(
            {
                "text": {"type": "plain_text", "text": f"{i + 1}. {title}"},
                "value": str(i),
            }
        )
    language_options = []
    for lang in languages:
        language_options.append(
            {
                "text": {"type": "plain_text", "text": lang["name"]},
                "value": lang["code"],
            }
        )
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📋 Source Selection*\n{response_text}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Found *{len(sources)}* sources. Select the ones you'd like to use for your podcast:",
            },
        },
    ]
    if source_options:
        blocks.append(
            {
                "type": "section",
                "block_id": "source_selection_block",
                "text": {"type": "mrkdwn", "text": "*Select Sources:*"},
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "source_selection",
                    "options": source_options,
                    "initial_options": source_options,
                },
            }
        )
    if len(sources) > 10:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Showing first 10 sources. {len(sources) - 10} more available._",
                    }
                ],
            }
        )
    blocks.extend(
        [
            {
                "type": "section",
                "block_id": "language_selection_block",
                "text": {"type": "mrkdwn", "text": "*Select Language:*"},
                "accessory": {
                    "type": "static_select",
                    "action_id": "language_selection",
                    "placeholder": {"type": "plain_text", "text": "Choose language"},
                    "options": language_options,
                    "initial_option": language_options[0] if language_options else None,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Confirm Selection"},
                        "style": "primary",
                        "action_id": "confirm_sources",
                        "value": thread_key,
                    }
                ],
            },
        ]
    )
    await send_slack_blocks(thread_key, blocks, "📋 Source Selection")