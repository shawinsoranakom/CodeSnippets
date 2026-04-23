def _save_podcast_to_database_sync(session_state: dict) -> tuple[bool, str, int]:
    try:
        if session_state.get("podcast_id"):
            return (
                True,
                f"Podcast already saved with ID: {session_state['podcast_id']}",
                session_state["podcast_id"],
            )
        tts_engine = session_state.get("tts_engine", "openai")
        podcast_info = session_state.get("podcast_info", {})
        generated_script = session_state.get("generated_script", {})
        banner_url = session_state.get("banner_url")
        banner_images = json.dumps(session_state.get("banner_images", []))
        audio_url = session_state.get("audio_url")
        selected_language = session_state.get("selected_language", {"code": "en", "name": "English"})
        language_code = selected_language.get("code", "en")
        if not generated_script or not isinstance(generated_script, dict):
            return (
                False,
                "Cannot complete podcast: Generated script is missing or invalid.",
                None,
            )
        if "title" not in generated_script:
            generated_script["title"] = podcast_info.get("topic", "Untitled Podcast")
        if "sections" not in generated_script or not isinstance(generated_script["sections"], list):
            return (
                False,
                "Cannot complete podcast: Generated script is missing required 'sections' array.",
                None,
            )
        sources = []
        if "sources" in generated_script and generated_script["sources"]:
            for source in generated_script["sources"]:
                if isinstance(source, str):
                    sources.append(source)
                elif isinstance(source, dict) and "url" in source:
                    sources.append(source["url"])
                elif isinstance(source, dict) and "link" in source:
                    sources.append(source["link"])
        generated_script["sources"] = sources
        db_path = get_podcasts_db_path()
        db_directory = DB_PATH
        os.makedirs(db_directory, exist_ok=True)

        conn = sqlite3.connect(db_path)
        content_json = json.dumps(generated_script)
        sources_json = json.dumps(sources) if sources else None
        current_time = datetime.now().isoformat()
        query = """
            INSERT INTO podcasts (
                title, 
                date, 
                content_json, 
                audio_generated, 
                audio_path,
                banner_img_path, 
                tts_engine, 
                language_code, 
                sources_json,
                created_at,
                banner_images
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        conn.execute(
            query,
            (
                generated_script.get("title", "Untitled Podcast"),
                datetime.now().strftime("%Y-%m-%d"),
                content_json,
                1 if audio_url else 0,
                audio_url,
                banner_url,
                tts_engine,
                language_code,
                sources_json,
                current_time,
                banner_images,
            ),
        )
        conn.commit()

        cursor = conn.execute("SELECT last_insert_rowid()")
        podcast_id = cursor.fetchone()
        podcast_id = podcast_id[0] if podcast_id else None
        cursor.close()
        conn.close()

        session_state["podcast_id"] = podcast_id
        return True, f"Podcast successfully saved with ID: {podcast_id}", podcast_id
    except Exception as e:
        print(f"Error saving podcast to database: {e}")
        return False, f"Error saving podcast to database: {str(e)}", None