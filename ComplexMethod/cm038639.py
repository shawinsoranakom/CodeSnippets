def _extract_system_message_from_request(
        self, request: ResponsesRequest
    ) -> str | None:
        system_msg = None
        if not isinstance(request.input, str):
            for response_msg in request.input:
                if (
                    isinstance(response_msg, dict)
                    and response_msg.get("role") == "system"
                ):
                    content = response_msg.get("content")
                    if isinstance(content, str):
                        system_msg = content
                    elif isinstance(content, list):
                        for param in content:
                            if (
                                isinstance(param, dict)
                                and param.get("type") == "input_text"
                            ):
                                system_msg = param.get("text")
                                break
                    break
        return system_msg