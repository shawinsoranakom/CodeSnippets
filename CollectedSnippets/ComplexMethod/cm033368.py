async def sse():
            nonlocal canvas
            contents: list[str] = []
            status = 200
            try:
                async for ans in canvas.run(
                    query="",
                    user_id=cvs.user_id,
                    webhook_payload=clean_request,
                ):
                    if ans["event"] == "message":
                        content = ans["data"]["content"]
                        if ans["data"].get("start_to_think", False):
                            content = "<think>"
                        elif ans["data"].get("end_to_think", False):
                            content = "</think>"
                        if content:
                            contents.append(content)
                    if ans["event"] == "message_end":
                        status = int(ans["data"].get("status", status))
                    if is_test:
                        append_webhook_trace(
                            agent_id,
                            start_ts,
                            ans
                        )
                if is_test:
                    append_webhook_trace(
                        agent_id,
                        start_ts,
                        {
                            "event": "finished",
                            "elapsed_time": time.time() - start_ts,
                            "success": True,
                        }
                    )
                final_content = "".join(contents)
                return {
                    "message": final_content,
                    "success": True,
                    "code":  status,
                }

            except Exception as e:
                if is_test:
                    append_webhook_trace(
                        agent_id,
                        start_ts,
                        {
                            "event": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                        }
                    )
                    append_webhook_trace(
                        agent_id,
                        start_ts,
                        {
                            "event": "finished",
                            "elapsed_time": time.time() - start_ts,
                            "success": False,
                        }
                    )
                return {"code": 400, "message": str(e),"success":False}