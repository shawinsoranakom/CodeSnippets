def _request_title_levels(title_aided_config, title_dict, prompt_builder=None):
    if len(title_dict) == 0:
        return {}

    client = OpenAI(
        api_key=title_aided_config["api_key"],
        base_url=title_aided_config["base_url"],
    )

    retry_count = 0
    max_retries = 3
    expected_keys = set(range(len(title_dict)))
    if prompt_builder is None:
        prompt_builder = _build_title_optimize_prompt
    title_optimize_prompt = prompt_builder(title_dict)

    logger.debug(f"Requesting LLM for title optimization with prompt: {title_optimize_prompt}")

    api_params = {
        "model": title_aided_config["model"],
        "messages": [{"role": "user", "content": title_optimize_prompt}],
        "temperature": 0.7,
        "stream": True,
    }
    if "enable_thinking" in title_aided_config:
        api_params["extra_body"] = {
            "enable_thinking": title_aided_config["enable_thinking"]
        }

    while retry_count < max_retries:
        try:
            completion = client.chat.completions.create(**api_params)
            content_pieces = []
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content_pieces.append(chunk.choices[0].delta.content)

            content = "".join(content_pieces).strip()
            if "</think>" in content:
                idx = content.index("</think>") + len("</think>")
                content = content[idx:].strip()

            logger.debug(f"Raw LLM output for title levels: {content}")
            dict_completion = json_repair.loads(content)
            dict_completion = {int(k): int(v) for k, v in dict_completion.items()}

            if set(dict_completion.keys()) == expected_keys:
                return dict_completion

            logger.warning(
                "The keys in the optimized title result do not match the input titles."
            )
        except Exception as e:
            logger.exception(e)

        retry_count += 1

    logger.error("Failed to decode dict after maximum retries.")
    return None