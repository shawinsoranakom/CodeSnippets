def process_confirmation():
        try:
            thread_key = body["actions"][0]["value"]
            user_id = body["user"]["id"]
            selected_sources = []
            selected_language = "en"
            if "state" in body and "values" in body["state"]:
                values = body["state"]["values"]
                if "source_selection_block" in values and "source_selection" in values["source_selection_block"]:
                    source_data = values["source_selection_block"]["source_selection"]
                    if "selected_options" in source_data and source_data["selected_options"]:
                        selected_sources = [int(opt["value"]) for opt in source_data["selected_options"]]
                if "language_selection_block" in values and "language_selection" in values["language_selection_block"]:
                    lang_data = values["language_selection_block"]["language_selection"]
                    if "selected_option" in lang_data and lang_data["selected_option"]:
                        selected_language = lang_data["selected_option"]["value"]
            session_info = get_session_info(thread_key)
            if not session_info:
                client.chat_postMessage(
                    channel=body["channel"]["id"],
                    thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                    text="❌ Session not found. Please start a new conversation.",
                )
                return
            session_id = session_info[0]
            state_data = get_session_state(session_id)
            languages = state_data.get("available_languages", [{"code": "en", "name": "English"}])
            language_name = next(
                (lang["name"] for lang in languages if lang["code"] == selected_language),
                "English",
            )
            sources = state_data.get("search_results", [])
            if selected_sources:
                source_indices = [str(i + 1) for i in selected_sources]
                selected_source_titles = [sources[i].get("title", f"Source {i + 1}") for i in selected_sources if i < len(sources)]
                message = f"I've selected sources {', '.join(source_indices)} and I want the podcast in {language_name}."
            else:
                source_indices = [str(i + 1) for i in range(len(sources))]
                selected_source_titles = [source.get("title", f"Source {i + 1}") for i, source in enumerate(sources)]
                message = f"I want the podcast in {language_name} using all available sources."
            try:
                confirmation_blocks = create_confirmation_blocks(
                    selected_sources,
                    selected_source_titles,
                    language_name,
                    len(sources),
                )
                client.chat_update(
                    channel=body["channel"]["id"],
                    ts=body["message"]["ts"],
                    blocks=confirmation_blocks,
                    text="✅ Selection Confirmed",
                )
                print(f"Updated interactive message to confirmation state for {thread_key}")
            except Exception as e:
                print(f"Error updating message: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text=f"🔄 Processing your selection: {message}\n\n_Generating podcast script..._",
            )
            asyncio.run(process_source_confirmation(thread_key, message))
        except Exception as e:
            print(f"Error in confirm_sources: {e}")
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=thread_key if not thread_key.startswith("dm_") else None,
                text="❌ Error processing your selection. Please try again.",
            )