def check_logprobs(cls, data):
        if (prompt_logprobs := data.get("prompt_logprobs")) is not None:
            if data.get("stream") and (prompt_logprobs > 0 or prompt_logprobs == -1):
                raise VLLMValidationError(
                    "`prompt_logprobs` are not available when `stream=True`.",
                    parameter="prompt_logprobs",
                )

            if prompt_logprobs < 0 and prompt_logprobs != -1:
                raise VLLMValidationError(
                    "`prompt_logprobs` must be a positive value or -1.",
                    parameter="prompt_logprobs",
                    value=prompt_logprobs,
                )
        if (top_logprobs := data.get("top_logprobs")) is not None:
            if top_logprobs < 0 and top_logprobs != -1:
                raise VLLMValidationError(
                    "`top_logprobs` must be a positive value or -1.",
                    parameter="top_logprobs",
                    value=top_logprobs,
                )

            if (top_logprobs == -1 or top_logprobs > 0) and not data.get("logprobs"):
                raise VLLMValidationError(
                    "when using `top_logprobs`, `logprobs` must be set to true.",
                    parameter="top_logprobs",
                )

        return data