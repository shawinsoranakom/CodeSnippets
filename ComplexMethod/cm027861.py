async def send_slack_message(thread_key: str, text: str):
    try:
        session_info = get_session_info(thread_key)
        if not session_info:
            print(f"No session info found for thread: {thread_key}")
            return
        session_id, channel_id, user_id = session_info
        if len(text) > 3800:
            chunks = [text[i : i + 3800] for i in range(0, len(text), 3800)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    if thread_key.startswith("dm_"):
                        app.client.chat_postMessage(channel=channel_id, text=chunk)
                    else:
                        app.client.chat_postMessage(channel=channel_id, text=chunk, thread_ts=thread_key)
                else:
                    if thread_key.startswith("dm_"):
                        app.client.chat_postMessage(channel=channel_id, text=f"...continued:\n{chunk}")
                    else:
                        app.client.chat_postMessage(
                            channel=channel_id,
                            text=f"...continued:\n{chunk}",
                            thread_ts=thread_key,
                        )
        else:
            if thread_key.startswith("dm_"):
                app.client.chat_postMessage(channel=channel_id, text=text)
            else:
                app.client.chat_postMessage(channel=channel_id, text=text, thread_ts=thread_key)
        print(f"Sent message to {thread_key}: {text[:50]}...")
    except Exception as e:
        print(f"Error sending Slack message: {e}")