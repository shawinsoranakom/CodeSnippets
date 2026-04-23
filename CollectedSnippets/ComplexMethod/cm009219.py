def _format_output(self, data: Any, **kwargs: Any) -> ChatResult:
        """Format the output from the Anthropic API to LC."""
        data_dict = data.model_dump()
        content = data_dict["content"]

        # Remove citations if they are None - introduced in anthropic sdk 0.45
        for block in content:
            if isinstance(block, dict):
                if "citations" in block and block["citations"] is None:
                    block.pop("citations")
                if "caller" in block and block["caller"] is None:
                    block.pop("caller")
                if "encrypted_content" in block and block["encrypted_content"] is None:
                    block.pop("encrypted_content")
                if (
                    block.get("type") == "thinking"
                    and "text" in block
                    and block["text"] is None
                ):
                    block.pop("text")

        llm_output = {
            k: v for k, v in data_dict.items() if k not in ("content", "role", "type")
        }
        if (
            (container := llm_output.get("container"))
            and isinstance(container, dict)
            and (expires_at := container.get("expires_at"))
            and isinstance(expires_at, datetime.datetime)
        ):
            # TODO: dump all `data` with `mode="json"`
            llm_output["container"]["expires_at"] = expires_at.isoformat()
        response_metadata = {"model_provider": "anthropic"}
        if "model" in llm_output and "model_name" not in llm_output:
            llm_output["model_name"] = llm_output["model"]
        if (
            len(content) == 1
            and content[0]["type"] == "text"
            and not content[0].get("citations")
        ):
            msg = AIMessage(
                content=content[0]["text"], response_metadata=response_metadata
            )
        elif any(block["type"] == "tool_use" for block in content):
            tool_calls = extract_tool_calls(content)
            msg = AIMessage(
                content=content,
                tool_calls=tool_calls,
                response_metadata=response_metadata,
            )
        else:
            msg = AIMessage(content=content, response_metadata=response_metadata)
        msg.usage_metadata = _create_usage_metadata(data.usage)
        return ChatResult(
            generations=[ChatGeneration(message=msg)],
            llm_output=llm_output,
        )