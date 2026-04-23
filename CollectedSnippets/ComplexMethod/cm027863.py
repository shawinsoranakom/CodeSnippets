async def handle_user_message(
    thread_key: str,
    user_input: str,
    say,
    channel_id: str,
    user_id: str,
    is_mention=False,
    is_dm=False,
):
    try:
        session_id = await get_or_create_session(thread_key, channel_id, user_id)
        session_state = get_session_state(session_id)
        if session_state.get("podcast_generated") and session_state.get("stage") == "complete":
            script = session_state.get("generated_script", {})
            podcast_title = script.get("title") if isinstance(script, dict) else "Your Podcast"
            podcast_id = session_state.get("podcast_id", "")
            completion_queries = ["download", "script", "audio", "banner", "share", "link", "asset", "file"]
            is_asset_query = any(query in user_input.lower() for query in completion_queries)
            if is_asset_query:
                completion_message = (
                    f"🎉 *'{podcast_title}' is complete!*\n\n"
                    "💡 *Looking for your podcast assets?*\n"
                    "All download links and assets were provided in the completion message above. "
                    "Please scroll up to find:\n"
                    "• Audio download link\n"
                    "• Banner images\n"
                    "• Complete script\n"
                    f"• Podcast ID: `{podcast_id}`\n\n"
                    "To create a **new podcast**, please start a fresh chat with me. 🎙️"
                )
            else:
                completion_message = (
                    f"🎉 *'{podcast_title}' is complete!*\n\n"
                    "This podcast session has finished successfully. To create a new podcast:\n\n"
                    "• **Start a new chat** with me\n"
                    "• Each podcast needs a fresh conversation\n"
                    "• Your completed podcast assets remain available above\n\n"
                    "Ready to create another amazing podcast? 🎙️✨"
                )
            if not is_dm and not is_mention:
                say(text=completion_message, thread_ts=thread_key)
            else:
                say(text=completion_message)
            print(f"Session {session_id} is complete - prevented API call for: {user_input[:50]}...")
            return
        if session_id in active_sessions:
            active_session = active_sessions[session_id]
            start_time = active_session.get("start_time", datetime.now())
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
            current_stage = session_state.get("stage", "unknown")
            process_type = active_session.get("process_type", "your request")
            stage_messages = {
                "search": "🔍 Searching for relevant sources",
                "scraping": "📰 Gathering full content from sources",
                "script": "📝 Generating podcast script",
                "banner": "🎨 Creating banner images",
                "image": "🎨 Creating banner images",
                "audio": "🎵 Generating podcast audio",
            }
            stage_message = stage_messages.get(current_stage, f"🔄 Processing {process_type}")
            progress_message = (
                f"⏳ *Still working on your podcast...*\n\n"
                f"{stage_message}\n"
                f"⏱️ Running for {elapsed_minutes:.1f} minutes\n\n"
                f"_Please wait while I complete this step. This can take several minutes for high-quality results._"
            )
            if current_stage == "search":
                progress_message += "\n\n💡 *Currently:* Finding the best sources across multiple platforms"
            elif current_stage == "script":
                progress_message += "\n\n💡 *Currently:* Crafting engaging dialogue and content structure"
            elif current_stage in ["banner", "image"]:
                progress_message += "\n\n💡 *Currently:* Generating professional banner designs"
            elif current_stage == "audio":
                progress_message += "\n\n💡 *Currently:* Creating high-quality voice narration"
            if not is_dm and not is_mention:
                say(text=progress_message, thread_ts=thread_key)
            else:
                say(text=progress_message)
            print(f"Session {session_id} already processing ({current_stage}) - prevented API call for: {user_input[:50]}...")
            return
        print(f"Processing message for session {session_id}: {user_input[:50]}...")
        chat_response = await api_client.chat(session_id, user_input)
        if chat_response.get("response"):
            response_text = chat_response["response"]
            if not is_dm and not is_mention:
                say(text=response_text, thread_ts=thread_key)
            else:
                say(text=response_text)
        if chat_response.get("is_processing"):
            task_id = chat_response.get("task_id")
            start_background_polling(session_id, thread_key, task_id)
            processing_msg = "🔄 Processing your request... This may take a moment."
            if not is_dm and not is_mention:
                say(text=processing_msg, thread_ts=thread_key)
            else:
                say(text=processing_msg)
        else:
            await send_completion_message(thread_key, chat_response)
    except Exception as e:
        print(f"Error handling message: {e}")
        if "timeout" in str(e).lower():
            error_msg = "⏱️ Request timed out. The system might be busy. Please try again in a moment."
        elif "connection" in str(e).lower():
            error_msg = "🔌 Connection issue. Please check your connection and try again."
        else:
            error_msg = "❌ Sorry, I encountered an error processing your request. Please try again."
        if not is_dm and not is_mention:
            say(text=error_msg, thread_ts=thread_key)
        else:
            say(text=error_msg)