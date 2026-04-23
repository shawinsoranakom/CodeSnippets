async def _get_chat_messages(self, row, session_id):
        formatted_messages = []
        session_state = {}
        if row["session_data"]:
            try:
                session = SessionService.get_session(session_id)
                session_state = session.get("state", {})
            except Exception as e:
                print(f"Error parsing session_data: {e}")

        if row["memory"]:
            try:
                memory_data = json.loads(row["memory"]) if isinstance(row["memory"], str) else row["memory"]
                if "runs" in memory_data and isinstance(memory_data["runs"], list):
                    for run in memory_data["runs"]:
                        if "messages" in run and isinstance(run["messages"], list):
                            for msg in run["messages"]:
                                if msg.get("role") in ["user", "assistant"] and "content" in msg:
                                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                                        if not msg.get("content"):
                                            continue
                                    if msg.get("content"):
                                        formatted_messages.append({"role": msg["role"], "content": msg["content"]})
            except json.JSONDecodeError as e:
                print(f"Error parsing memory data: {e}")

        return formatted_messages, session_state