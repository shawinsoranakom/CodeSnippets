async def execute(self, code: str, timeout_seconds: Optional[float] = None) -> ExecutionResult:
        message_id = await self._send_message(
            content={
                "code": code,
                "silent": False,
                "store_history": True,
                "user_expressions": {},
                "allow_stdin": False,
                "stop_on_error": True,
            },
            channel="shell",
            message_type="execute_request",
        )

        text_output: List[str] = []
        data_output: List[DataItem] = []
        while True:
            message = await self._receive_message(timeout_seconds)
            if message is None:
                return ExecutionResult(
                    is_ok=False, output="ERROR: Timeout waiting for output from code block.", data_items=[]
                )

            # Ignore messages that are not for this execution.
            if message.get("parent_header", {}).get("msg_id") != message_id:
                continue

            msg_type = message["msg_type"]
            content = message["content"]
            if msg_type in ["execute_result", "display_data"]:
                for data_type, data in content["data"].items():
                    if data_type == "text/plain":
                        text_output.append(data)
                    elif data_type.startswith("image/") or data_type == "text/html":
                        data_output.append(DataItem(mime_type=data_type, data=data))
                    else:
                        text_output.append(json.dumps(data))
            elif msg_type == "stream":
                text_output.append(content["text"])
            elif msg_type == "error":
                # Output is an error.
                return ExecutionResult(
                    is_ok=False,
                    output=f"ERROR: {content['ename']}: {content['evalue']}\n{content['traceback']}",
                    data_items=[],
                )
            if msg_type == "status" and content["execution_state"] == "idle":
                break
        return ExecutionResult(
            is_ok=True, output="\n".join([str(output) for output in text_output]), data_items=data_output
        )