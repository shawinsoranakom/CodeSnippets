async def delete_session(self, session_id: str):
        try:
            db_path = get_agent_session_db_path()
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                async with conn.execute("SELECT session_data FROM podcast_sessions WHERE session_id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": f"Session with ID {session_id} not found"})
                try:
                    session = SessionService.get_session(session_id)
                    session_state = session.get("state", {})
                    stage = session_state.get("stage")
                    is_completed = stage == "complete" or session_state.get("podcast_generated", False)
                    banner_url = session_state.get("banner_url")
                    audio_url = session_state.get("audio_url")
                    web_search_recording = session_state.get("web_search_recording")
                    await conn.execute("DELETE FROM podcast_sessions WHERE session_id = ?", (session_id,))
                    await conn.commit()
                    if is_completed:
                        print(f"Session {session_id} is in 'complete' stage, keeping assets but removing session record")
                    else:
                        if banner_url:
                            banner_path = os.path.join(PODCAST_IMG_DIR, banner_url)
                            if os.path.exists(banner_path):
                                try:
                                    os.remove(banner_path)
                                    print(f"Deleted banner image: {banner_path}")
                                except Exception as e:
                                    print(f"Error deleting banner image: {e}")
                        if audio_url:
                            audio_path = os.path.join(PODCAST_AUIDO_DIR, audio_url)
                            if os.path.exists(audio_path):
                                try:
                                    os.remove(audio_path)
                                    print(f"Deleted audio file: {audio_path}")
                                except Exception as e:
                                    print(f"Error deleting audio file: {e}")
                        if web_search_recording:
                            recording_dir = os.path.join(PODCAST_RECORDINGS_DIR, session_id)
                            if os.path.exists(recording_dir):
                                try:
                                    import shutil

                                    shutil.rmtree(recording_dir)
                                    print(f"Deleted recordings directory: {recording_dir}")
                                except Exception as e:
                                    print(f"Error deleting recordings directory: {e}")
                    if is_completed:
                        return {"success": True, "message": f"Session {session_id} deleted, but assets preserved"}
                    else:
                        return {"success": True, "message": f"Session {session_id} and its associated data deleted successfully"}
                except Exception as e:
                    print(f"Error parsing session data for deletion: {e}")
                    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Error deleting session: {str(e)}"})
        except Exception as e:
            print(f"Error deleting session: {e}")
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Failed to delete session: {str(e)}"})