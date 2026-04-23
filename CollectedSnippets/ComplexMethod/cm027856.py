async def poll_for_completion(session_id: str, thread_key: str, task_id=None):
    print(f"Starting polling for session: {session_id}, task: {task_id}")
    max_polls = 60
    poll_count = 0
    active_sessions[session_id] = {
        "thread_key": thread_key,
        "task_id": task_id,
        "start_time": datetime.now(),
    }
    try:
        while poll_count < max_polls:
            try:
                status_response = await api_client.check_status(session_id, task_id)
                if status_response.get("session_state"):
                    save_session_state(session_id, status_response.get("session_state"))
                if not status_response.get("is_processing", True):
                    await send_completion_message(thread_key, status_response)
                    break
                if poll_count % 10 == 0 and poll_count > 0:
                    process_type = status_response.get("process_type", "request")
                    await send_slack_message(
                        thread_key,
                        f"🔄 Still processing {process_type}... ({poll_count * 3}s elapsed)",
                    )
                await asyncio.sleep(3)
                poll_count += 1
            except Exception as e:
                print(f"Polling error: {e}")
                await send_slack_message(
                    thread_key,
                    "❌ Something went wrong while processing your request. Please try again.",
                )
                break
    finally:
        if session_id in active_sessions:
            del active_sessions[session_id]