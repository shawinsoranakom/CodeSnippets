def _apply_model_family_policies(
    model_name: str,
    *,
    backend: str,
    provider: SupportedLiteLLMProvider | str | None = None,
    gen_conf: dict | None = None,
    request_kwargs: dict | None = None,
):
    model_name_lower = (model_name or "").lower()
    sanitized_gen_conf = deepcopy(gen_conf) if gen_conf else {}
    sanitized_kwargs = dict(request_kwargs) if request_kwargs else {}

    # Qwen3 family disables thinking by extra_body on non-stream chat requests.
    if "qwen3" in model_name_lower:
        sanitized_kwargs["extra_body"] = {"enable_thinking": False}

    if backend == "base":
        return sanitized_gen_conf, sanitized_kwargs

    if backend == "litellm":
        if provider in {SupportedLiteLLMProvider.OpenAI, SupportedLiteLLMProvider.Azure_OpenAI} and "gpt-5" in model_name_lower:
            for key in ("temperature", "top_p", "logprobs", "top_logprobs"):
                sanitized_gen_conf.pop(key, None)
                sanitized_kwargs.pop(key, None)

        if provider == SupportedLiteLLMProvider.HunYuan:
            for key in ("presence_penalty", "frequency_penalty"):
                sanitized_gen_conf.pop(key, None)
        elif "kimi-k2.5" in model_name_lower:
            reasoning = sanitized_gen_conf.pop("reasoning", None)
            thinking = {"type": "enabled"}
            if reasoning is not None:
                thinking = {"type": "enabled"} if reasoning else {"type": "disabled"}
            elif not isinstance(thinking, dict) or thinking.get("type") not in {"enabled", "disabled"}:
                thinking = {"type": "disabled"}
            sanitized_gen_conf["thinking"] = thinking

            thinking_enabled = thinking.get("type") == "enabled"
            sanitized_gen_conf["temperature"] = 1.0 if thinking_enabled else 0.6
            sanitized_gen_conf["top_p"] = 0.95
            sanitized_gen_conf["n"] = 1
            sanitized_gen_conf["presence_penalty"] = 0.0
            sanitized_gen_conf["frequency_penalty"] = 0.0

        return sanitized_gen_conf, sanitized_kwargs

    return sanitized_gen_conf, sanitized_kwargs