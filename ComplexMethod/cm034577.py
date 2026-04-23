def __init__(
        self,
        promptTokens: int = None,
        completionTokens: int = None,
        input_tokens: int = None,
        output_tokens: int = None,
        output_tokens_details: Dict = None,
        promptTokenCount: int = None,
        candidatesTokenCount: int = None,
        totalTokenCount: int = None,
        **kwargs
    ):
        if promptTokens is not None:
            kwargs["prompt_tokens"] = promptTokens
        if completionTokens is not None:
            kwargs["completion_tokens"] = completionTokens
        if input_tokens is not None:
            kwargs["prompt_tokens"] = input_tokens
        if output_tokens is not None:
            kwargs["completion_tokens"] = output_tokens
        if promptTokenCount is not None:
            kwargs["prompt_tokens"] = promptTokenCount
        if candidatesTokenCount is not None:
            kwargs["completion_tokens"] = candidatesTokenCount
        if totalTokenCount is not None:
            kwargs["total_tokens"] = totalTokenCount
        if output_tokens_details is not None:
            for key, value in output_tokens_details.items():
                kwargs[key] = value
        if "total_tokens" not in kwargs and "prompt_tokens" in kwargs and "completion_tokens" in kwargs:
            kwargs["total_tokens"] = kwargs["prompt_tokens"] + kwargs["completion_tokens"]
        return super().__init__(**kwargs)