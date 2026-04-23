def fetch_video_data(video_url: str) -> Tuple[str, str]:
    try:
        video_id = extract_video_id(video_url)

        # Create API instance (required for new version)
        api = YouTubeTranscriptApi()

        # First, check if transcripts are available
        try:
            transcript_list = api.list(video_id)
            available_languages = [t.language_code for t in transcript_list]
            st.info(f"Available transcripts: {available_languages}")
        except Exception as list_error:
            st.error(f"Cannot retrieve transcript list: {list_error}")
            return "Unknown", "No transcript available for this video."

        # Try to get transcript with multiple fallback languages
        languages_to_try = ['en', 'en-US', 'en-GB']  # Try English variants first
        transcript = None

        for lang in languages_to_try:
            if lang in available_languages:
                try:
                    fetched_transcript = api.fetch(video_id, languages=[lang])
                    transcript = list(fetched_transcript)  # Convert to list of snippets
                    st.success(f"Successfully fetched transcript in language: {lang}")
                    break
                except Exception:
                    continue

        # If no English transcript, try any available language
        if transcript is None and available_languages:
            try:
                fetched_transcript = api.fetch(video_id, languages=[available_languages[0]])
                transcript = list(fetched_transcript)
                st.success(f"Successfully fetched transcript in language: {available_languages[0]}")
            except Exception as final_error:
                st.error(f"Could not fetch transcript in any language: {final_error}")
                return "Unknown", "No transcript available for this video."

        if transcript:
            # Extract text from FetchedTranscriptSnippet objects
            transcript_text = " ".join([snippet.text for snippet in transcript])
            return "Unknown", transcript_text  # Title is set to "Unknown" since we're not fetching it
        else:
            return "Unknown", "No transcript available for this video."

    except ValueError as ve:
        st.error(f"Invalid YouTube URL: {ve}")
        return "Unknown", "Invalid YouTube URL provided."
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        if "VideoUnavailable" in error_type:
            st.error("❌ Video is unavailable, private, or has been removed.")
        elif "TranscriptsDisabled" in error_type:
            st.error("❌ Subtitles/transcripts are disabled for this video.")
            st.info("💡 Try a different video that has subtitles enabled.")
        elif "NoTranscriptFound" in error_type:
            st.error("❌ No transcript found in the requested language.")
            st.info("💡 Try a video with auto-generated subtitles or manual captions.")
        elif "ParseError" in error_type:
            st.error("❌ Unable to parse video data. This might be due to:")
            st.info("• Video is private or restricted")
            st.info("• Video has been removed")
            st.info("• YouTube changed their format")
            st.info("💡 Try a different video.")
        else:
            st.error(f"❌ Error fetching transcript ({error_type}): {error_msg}")

        return "Unknown", "No transcript available for this video."