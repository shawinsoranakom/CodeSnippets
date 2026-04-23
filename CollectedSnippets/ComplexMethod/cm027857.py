async def send_completion_message(thread_key: str, status_response):
    response_text = status_response.get("response", "Task completed!")
    session_state = status_response.get("session_state")
    if session_state:
        try:
            state_data = json.loads(session_state) if isinstance(session_state, str) else session_state
            if state_data.get("show_sources_for_selection") and state_data.get("search_results"):
                await send_source_selection_blocks(thread_key, state_data, response_text)
            elif state_data.get("show_script_for_confirmation") and state_data.get("generated_script"):
                await send_script_confirmation_blocks(thread_key, state_data, response_text)
            elif state_data.get("show_banner_for_confirmation") and state_data.get("banner_url"):
                await send_banner_confirmation_blocks(thread_key, state_data, response_text)
            elif state_data.get("show_audio_for_confirmation") and state_data.get("audio_url"):
                await send_audio_confirmation_blocks(thread_key, state_data, response_text)
            elif state_data.get("podcast_generated"):
                await send_final_presentation_blocks(thread_key, state_data, response_text)
            else:
                await send_slack_message(thread_key, response_text)
        except Exception as e:
            print(f"Error parsing session state: {e}")
            await send_slack_message(thread_key, response_text)
    else:
        await send_slack_message(thread_key, response_text)