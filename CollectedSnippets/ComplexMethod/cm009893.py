def _load_llm_math_chain(config: dict, **kwargs: Any) -> LLMMathChain:
    llm_chain = None
    if "llm_chain" in config:
        llm_chain_config = config.pop("llm_chain")
        llm_chain = load_chain_from_config(llm_chain_config, **kwargs)
    elif "llm_chain_path" in config:
        llm_chain = load_chain(config.pop("llm_chain_path"), **kwargs)
    # llm attribute is deprecated in favor of llm_chain, here to support old configs
    elif "llm" in config:
        llm_config = config.pop("llm")
        llm = load_llm_from_config(llm_config, **kwargs)
    # llm_path attribute is deprecated in favor of llm_chain_path,
    # its to support old configs
    elif "llm_path" in config:
        llm = load_llm(config.pop("llm_path"), **kwargs)
    else:
        msg = "One of `llm_chain` or `llm_chain_path` must be present."
        raise ValueError(msg)
    if "prompt" in config:
        prompt_config = config.pop("prompt")
        prompt = load_prompt_from_config(prompt_config)
    elif "prompt_path" in config:
        prompt = load_prompt(config.pop("prompt_path"))
    if llm_chain:
        return LLMMathChain(llm_chain=llm_chain, prompt=prompt, **config)
    return LLMMathChain(llm=llm, prompt=prompt, **config)