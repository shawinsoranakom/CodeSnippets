def _create_chat_result(
        self,
        response: dict | openai.BaseModel,
        generation_info: dict | None = None,
    ) -> ChatResult:
        generations = []

        response_dict = (
            response
            if isinstance(response, dict)
            # `parsed` may hold arbitrary Pydantic models from structured output.
            # Exclude it from this dump and copy it from the typed response below.
            else response.model_dump(
                exclude={"choices": {"__all__": {"message": {"parsed"}}}}
            )
        )
        # Sometimes the AI Model calling will get error, we should raise it (this is
        # typically followed by a null value for `choices`, which we raise for
        # separately below).
        if response_dict.get("error"):
            raise ValueError(response_dict.get("error"))

        # Raise informative error messages for non-OpenAI chat completions APIs
        # that return malformed responses.
        try:
            choices = response_dict["choices"]
        except KeyError as e:
            msg = f"Response missing 'choices' key: {response_dict.keys()}"
            raise KeyError(msg) from e

        if choices is None:
            # Some OpenAI-compatible APIs (e.g., vLLM) may return null choices
            # when the response format differs or an error occurs without
            # populating the error field. Provide a more helpful error message.
            msg = (
                "Received response with null value for 'choices'. "
                "This can happen when using OpenAI-compatible APIs (e.g., vLLM) "
                "that return a response in an unexpected format. "
                f"Full response keys: {list(response_dict.keys())}"
            )
            raise TypeError(msg)

        token_usage = response_dict.get("usage")
        service_tier = response_dict.get("service_tier")

        for res in choices:
            message = _convert_dict_to_message(res["message"])
            if token_usage and isinstance(message, AIMessage):
                message.usage_metadata = _create_usage_metadata(
                    token_usage, service_tier
                )
            generation_info = generation_info or {}
            generation_info["finish_reason"] = (
                res.get("finish_reason")
                if res.get("finish_reason") is not None
                else generation_info.get("finish_reason")
            )
            if "logprobs" in res:
                generation_info["logprobs"] = res["logprobs"]
            gen = ChatGeneration(message=message, generation_info=generation_info)
            generations.append(gen)
        llm_output = {
            "token_usage": token_usage,
            "model_provider": "openai",
            "model_name": response_dict.get("model", self.model_name),
            "system_fingerprint": response_dict.get("system_fingerprint", ""),
        }
        if "id" in response_dict:
            llm_output["id"] = response_dict["id"]
        if service_tier:
            llm_output["service_tier"] = service_tier

        if isinstance(response, openai.BaseModel) and getattr(
            response, "choices", None
        ):
            message = response.choices[0].message  # type: ignore[attr-defined]
            if hasattr(message, "parsed"):
                generations[0].message.additional_kwargs["parsed"] = message.parsed
            if hasattr(message, "refusal"):
                generations[0].message.additional_kwargs["refusal"] = message.refusal

        return ChatResult(generations=generations, llm_output=llm_output)