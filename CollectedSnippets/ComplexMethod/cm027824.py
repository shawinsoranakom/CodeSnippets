async def check_result_status(self, request):
        try:
            if not request.session_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Session ID is required"},
                )

            browser_recording_path = self._browser_recording(request.session_id)

            task_id = getattr(request, "task_id", None)
            if task_id:
                task = agent_chat.AsyncResult(task_id)
                if task.state == "PENDING" or task.state == "STARTED":
                    return {
                        "session_id": request.session_id,
                        "response": "Your request is still being processed.",
                        "stage": "processing",
                        "session_state": "{}",
                        "is_processing": True,
                        "process_type": "chat",
                        "task_id": task_id,
                        "browser_recording_path": browser_recording_path,
                    }
                elif task.state == "SUCCESS":
                    result = task.result
                    if result and isinstance(result, dict):
                        if result.get("session_id") != request.session_id:
                            return {
                                "session_id": request.session_id,
                                "response": "Error: Received result for wrong session.",
                                "stage": "error",
                                "session_state": "{}",
                                "is_processing": False,
                                "browser_recording_path": browser_recording_path,
                            }
                        return result
                else:
                    error_info = str(task.result) if task.result else f"Task failed with state: {task.state}"
                    return {
                        "session_id": request.session_id,
                        "response": f"Error processing request: {error_info}",
                        "stage": "error",
                        "session_state": "{}",
                        "is_processing": False,
                        "browser_recording_path": browser_recording_path,
                    }
            return await self.get_session_state(request.session_id)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": f"Error checking result status: {str(e)}",
                    "session_id": request.session_id,
                    "response": f"Error checking result status: {str(e)}",
                    "stage": "error",
                    "session_state": "{}",
                    "is_processing": False,
                    "browser_recording_path": browser_recording_path,
                },
            )