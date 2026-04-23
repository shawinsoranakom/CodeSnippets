async def cmd_load(session_ids: list[str]) -> None:
    """Load downloaded transcripts into local workspace storage + DB."""
    from backend.copilot.sdk.transcript import upload_transcript

    # Use the user_id from meta file or env var
    default_user_id = os.environ.get("USER_ID", "")

    for sid in session_ids:
        transcript_file = _transcript_path(sid)
        meta_file = _meta_path(sid)

        if not os.path.exists(transcript_file):
            print(f"[{sid[:12]}] No transcript file at {transcript_file}")
            print("  Run 'download' first, or place the file manually.")
            continue

        with open(transcript_file) as f:
            content = f.read()

        # Load meta if available
        user_id = default_user_id
        msg_count = 0
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                meta = json.load(f)
            user_id = meta.get("user_id", user_id)
            msg_count = meta.get("message_count", 0)

        if not user_id:
            print(f"[{sid[:12]}] No user_id — set USER_ID env var or download first")
            continue

        lines = len(content.strip().split("\n"))
        print(f"[{sid[:12]}] Loading transcript: {lines} entries, {len(content)} bytes")

        # Parse messages from transcript for DB
        messages = _parse_messages_from_transcript(content)
        if not msg_count:
            msg_count = len(messages)
        print(f"[{sid[:12]}] Parsed {len(messages)} messages for DB")

        # Create chat session in DB
        try:
            from backend.copilot.db import create_chat_session, get_chat_session

            existing = await get_chat_session(sid)
            if existing:
                print(f"[{sid[:12]}] Session already exists in DB, skipping creation")
            else:
                await create_chat_session(sid, user_id)
                print(f"[{sid[:12]}] Created ChatSession in DB")
        except Exception as e:
            print(f"[{sid[:12]}] DB session creation failed: {e}")
            print("  You may need to create it manually or run with DB access.")

        # Add messages to DB
        if messages:
            try:
                from backend.copilot.db import add_chat_messages_batch

                msg_dicts = [
                    {"role": m["role"], "content": m["content"]} for m in messages
                ]
                await add_chat_messages_batch(sid, msg_dicts, start_sequence=0)
                print(f"[{sid[:12]}] Added {len(messages)} messages to DB")
            except Exception as e:
                print(f"[{sid[:12]}] Message insertion failed: {e}")
                print("  (Session may already have messages)")

        # Store transcript in local workspace storage
        try:
            await upload_transcript(
                user_id=user_id,
                session_id=sid,
                content=content.encode("utf-8"),
                message_count=msg_count,
            )
            print(f"[{sid[:12]}] Stored transcript in local workspace storage")
        except Exception as e:
            print(f"[{sid[:12]}] Transcript storage failed: {e}")

        # Also store directly to filesystem as fallback
        try:
            from backend.util.settings import Settings

            settings = Settings()
            storage_dir = settings.config.workspace_storage_dir or os.path.join(
                os.path.expanduser("~"), ".autogpt", "workspaces"
            )
            ts_dir = os.path.join(storage_dir, "chat-transcripts", _sanitize(user_id))
            os.makedirs(ts_dir, exist_ok=True)

            ts_path = os.path.join(ts_dir, f"{_sanitize(sid)}.jsonl")
            with open(ts_path, "w") as f:
                f.write(content)

            meta_storage = {
                "message_count": msg_count,
                "uploaded_at": time.time(),
            }
            meta_storage_path = os.path.join(ts_dir, f"{_sanitize(sid)}.meta.json")
            with open(meta_storage_path, "w") as f:
                json.dump(meta_storage, f)

            print(f"[{sid[:12]}] Also wrote to: {ts_path}")
        except Exception as e:
            print(f"[{sid[:12]}] Direct file write failed: {e}")

        print(f"[{sid[:12]}] Ready — send a message to this session to test")
        print()

    print("Done. Start the backend and send a message to the session(s).")
    print("The CoPilot will use --resume with the loaded transcript.")