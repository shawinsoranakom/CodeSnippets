def validate_transcription_request(cls, data):
        if isinstance(data.get("file"), str):
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Expected 'file' to be a file-like object, not 'str'.",
            )

        stream_opts = ["stream_include_usage", "stream_continuous_usage_stats"]
        stream = data.get("stream", False)
        if any(bool(data.get(so, False)) for so in stream_opts) and not stream:
            # Find which specific stream option was set
            invalid_param = next(
                (so for so in stream_opts if data.get(so, False)),
                "stream_include_usage",
            )
            raise VLLMValidationError(
                "Stream options can only be defined when `stream=True`.",
                parameter=invalid_param,
            )

        # Parse vllm_xargs from JSON string (form data sends it as a string)
        xargs = data.get("vllm_xargs")
        if isinstance(xargs, str):
            try:
                data["vllm_xargs"] = json.loads(xargs)
            except json.JSONDecodeError as e:
                raise VLLMValidationError(
                    f"Failed to parse vllm_xargs. Must be valid JSON: {e}",
                    parameter="vllm_xargs",
                ) from e

        return data