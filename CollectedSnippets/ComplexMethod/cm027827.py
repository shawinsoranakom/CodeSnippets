async def get_session_history(self, session_id: str):
        try:
            db_path = get_agent_session_db_path()
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                async with conn.execute(
                    """
                    select name from sqlite_master
                    where type='table' and name='podcast_sessions'
                    """
                ) as cursor:
                    table = await cursor.fetchone()
                    if not table:
                        return {"session_id": session_id, "messages": [], "state": "{}", "is_processing": False, "process_type": None}
                async with conn.execute("SELECT memory, session_data FROM podcast_sessions WHERE session_id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    return {"session_id": session_id, "messages": [], "state": "{}", "is_processing": False, "process_type": None}
                formatted_messages, session_state = await self._get_chat_messages(row, session_id)

            task_id = await self.get_active_task(session_id)
            is_processing = bool(task_id)
            process_type = "chat" if is_processing else None
            browser_recording_path = self._browser_recording(session_id)

            return {
                "session_id": session_id,
                "messages": formatted_messages,
                "state": json.dumps(session_state),
                "is_processing": is_processing,
                "process_type": process_type,
                "task_id": task_id if task_id and is_processing else None,
                "browser_recording_path": browser_recording_path,
            }
        except Exception as e:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Error retrieving session history: {str(e)}"})