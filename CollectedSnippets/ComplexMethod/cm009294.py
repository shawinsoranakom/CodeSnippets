def _create_chat_result(self, response: Any) -> ChatResult:  # noqa: C901, PLR0912
        """Create a `ChatResult` from an OpenRouter SDK response."""
        if not isinstance(response, dict):
            response = response.model_dump(by_alias=True)

        if error := response.get("error"):
            msg = (
                f"OpenRouter API returned an error: "
                f"{error.get('message', str(error))} "
                f"(code: {error.get('code', 'unknown')})"
            )
            raise ValueError(msg)

        generations = []
        token_usage = response.get("usage") or {}

        choices = response.get("choices", [])
        if not choices:
            msg = (
                "OpenRouter API returned a response with no choices. "
                "This may indicate a problem with the request or model availability."
            )
            raise ValueError(msg)

        # Extract top-level response metadata
        response_model = response.get("model")
        system_fingerprint = response.get("system_fingerprint")

        for res in choices:
            message = _convert_dict_to_message(res["message"])
            if token_usage and isinstance(message, AIMessage):
                message.usage_metadata = _create_usage_metadata(token_usage)
                # Surface OpenRouter cost data in response_metadata
                if "cost" in token_usage:
                    message.response_metadata["cost"] = token_usage["cost"]
                if "cost_details" in token_usage:
                    message.response_metadata["cost_details"] = token_usage[
                        "cost_details"
                    ]
            if isinstance(message, AIMessage):
                if system_fingerprint:
                    message.response_metadata["system_fingerprint"] = system_fingerprint
                if native_finish_reason := res.get("native_finish_reason"):
                    message.response_metadata["native_finish_reason"] = (
                        native_finish_reason
                    )
            generation_info: dict[str, Any] = {
                "finish_reason": res.get("finish_reason"),
            }
            if "logprobs" in res:
                generation_info["logprobs"] = res["logprobs"]
            gen = ChatGeneration(
                message=message,
                generation_info=generation_info,
            )
            generations.append(gen)

        llm_output: dict[str, Any] = {
            "model_name": response_model or self.model_name,
        }
        if response_id := response.get("id"):
            llm_output["id"] = response_id
        if created := response.get("created"):
            llm_output["created"] = int(created)
        if object_ := response.get("object"):
            llm_output["object"] = object_
        return ChatResult(generations=generations, llm_output=llm_output)