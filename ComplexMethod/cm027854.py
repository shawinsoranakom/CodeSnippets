def audio_generate_agent_run(agent: Agent) -> str:
    """
    Generate an audio file for the podcast using the selected TTS engine.

    Args:
        agent: The agent instance

    Returns:
        A message with the result of audio generation
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    script_data = session_state.get("generated_script", {})
    if not script_data or (isinstance(script_data, dict) and not script_data.get("sections")):
        error_msg = "Cannot generate audio: No podcast script data found. Please generate a script first."
        print(error_msg)
        return error_msg
    if isinstance(script_data, dict):
        podcast_title = script_data.get("title", "Your Podcast")
    else:
        podcast_title = "Your Podcast"
    session_state["stage"] = "audio"
    audio_dir = PODCAST_AUDIO_FOLDER
    audio_filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_path = os.path.join(audio_dir, audio_filename)
    try:
        if isinstance(script_data, dict) and "sections" in script_data:
            speaker_map = {"ALEX": 1, "MORGAN": 2}
            script_entries = []
            for section in script_data.get("sections", []):
                for dialog in section.get("dialog", []):
                    speaker = dialog.get("speaker", "ALEX")
                    text = dialog.get("text", "")

                    if text and speaker in speaker_map:
                        script_entries.append({"text": text, "speaker": speaker_map[speaker]})
            if not script_entries:
                error_msg = "Cannot generate audio: No dialog found in the script."
                print(error_msg)
                return error_msg

            selected_language = session_state.get("selected_language", {"code": "en", "name": "English"})
            language_code = selected_language.get("code", "en")
            language_name = selected_language.get("name", "English")
            tts_engine = "openai"
            if tts_engine == "openai" and not load_api_key("OPENAI_API_KEY"):
                error_msg = "Cannot generate audio: OpenAI API key not found."
                print(error_msg)
                return error_msg
            print(f"Generating podcast audio using {tts_engine} TTS engine in {language_name} language")
            full_audio_path = create_podcast(
                script=script_entries,
                output_path=audio_path,
                tts_engine=tts_engine,
                language_code=language_code,
            )
            if not full_audio_path:
                error_msg = f"Failed to generate podcast audio with {tts_engine} TTS engine."
                print(error_msg)
                return error_msg

            audio_url = f"{os.path.basename(full_audio_path)}"
            session_state["audio_url"] = audio_url
            session_state["show_audio_for_confirmation"] = True
            SessionService.save_session(session_id, session_state)
            print(f"Successfully generated podcast audio: {full_audio_path}")
            return f"I've generated the audio for your '{podcast_title}' podcast using {tts_engine.capitalize()} voices in {language_name}. You can listen to it in the player below. What do you think? If it sounds good, click 'Sounds Great!' to complete your podcast."
        else:
            error_msg = "Cannot generate audio: Script is not in the expected format."
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Error generating podcast audio: {str(e)}"
        print(error_msg)
        return f"I encountered an error while generating the podcast audio: {str(e)}. Please try again or let me know if you'd like to proceed without audio."