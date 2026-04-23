def _load_llm_checker_chain(config: dict, **kwargs: Any) -> LLMCheckerChain:
    if "llm" in config:
        llm_config = config.pop("llm")
        llm = load_llm_from_config(llm_config, **kwargs)
    elif "llm_path" in config:
        llm = load_llm(config.pop("llm_path"), **kwargs)
    else:
        msg = "One of `llm` or `llm_path` must be present."
        raise ValueError(msg)
    if "create_draft_answer_prompt" in config:
        create_draft_answer_prompt_config = config.pop("create_draft_answer_prompt")
        create_draft_answer_prompt = load_prompt_from_config(
            create_draft_answer_prompt_config,
        )
    elif "create_draft_answer_prompt_path" in config:
        create_draft_answer_prompt = load_prompt(
            config.pop("create_draft_answer_prompt_path"),
        )
    if "list_assertions_prompt" in config:
        list_assertions_prompt_config = config.pop("list_assertions_prompt")
        list_assertions_prompt = load_prompt_from_config(list_assertions_prompt_config)
    elif "list_assertions_prompt_path" in config:
        list_assertions_prompt = load_prompt(config.pop("list_assertions_prompt_path"))
    if "check_assertions_prompt" in config:
        check_assertions_prompt_config = config.pop("check_assertions_prompt")
        check_assertions_prompt = load_prompt_from_config(
            check_assertions_prompt_config,
        )
    elif "check_assertions_prompt_path" in config:
        check_assertions_prompt = load_prompt(
            config.pop("check_assertions_prompt_path"),
        )
    if "revised_answer_prompt" in config:
        revised_answer_prompt_config = config.pop("revised_answer_prompt")
        revised_answer_prompt = load_prompt_from_config(revised_answer_prompt_config)
    elif "revised_answer_prompt_path" in config:
        revised_answer_prompt = load_prompt(config.pop("revised_answer_prompt_path"))
    return LLMCheckerChain(
        llm=llm,
        create_draft_answer_prompt=create_draft_answer_prompt,
        list_assertions_prompt=list_assertions_prompt,
        check_assertions_prompt=check_assertions_prompt,
        revised_answer_prompt=revised_answer_prompt,
        **config,
    )