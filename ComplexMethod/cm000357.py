async def cmd_download(session_ids: list[str]) -> None:
    """Download transcripts from prod GCS to transcripts/ directory."""
    from backend.copilot.sdk.transcript import download_transcript

    user_id = os.environ.get("USER_ID", "")
    if not user_id:
        print("ERROR: Set USER_ID env var to the session owner's user ID.")
        print("  You can find it in Sentry breadcrumbs or the DB.")
        sys.exit(1)

    bucket = os.environ.get("MEDIA_GCS_BUCKET_NAME", "")
    if not bucket:
        print("ERROR: Set MEDIA_GCS_BUCKET_NAME to the prod GCS bucket.")
        sys.exit(1)

    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    print(f"Downloading from GCS bucket: {bucket}")
    print(f"User ID: {user_id}\n")

    for sid in session_ids:
        print(f"[{sid[:12]}] Downloading...")
        try:
            dl = await download_transcript(user_id, sid)
        except Exception as e:
            print(f"[{sid[:12]}] Failed: {e}")
            continue

        if not dl or not dl.content:
            print(f"[{sid[:12]}] Not found in GCS")
            continue

        content_str = (
            dl.content.decode("utf-8") if isinstance(dl.content, bytes) else dl.content
        )
        out = _transcript_path(sid)
        with open(out, "w") as f:
            f.write(content_str)

        lines = len(content_str.strip().split("\n"))
        meta = {
            "session_id": sid,
            "user_id": user_id,
            "message_count": dl.message_count,
            "transcript_bytes": len(content_str),
            "transcript_lines": lines,
        }
        with open(_meta_path(sid), "w") as f:
            json.dump(meta, f, indent=2)

        print(
            f"[{sid[:12]}] Saved: {lines} entries, "
            f"{len(content_str)} bytes, msg_count={dl.message_count}"
        )
    print("\nDone. Run 'load' command to import into local dev environment.")