def get_template_and_fix_tokenizer(tokenizer: "PreTrainedTokenizer", data_args: "DataArguments") -> "Template":
    r"""Get chat template and fixes the tokenizer."""
    if data_args.template is None:
        if isinstance(tokenizer.chat_template, str):
            logger.warning_rank0("`template` was not specified, try parsing the chat template from the tokenizer.")
            template = parse_template(tokenizer)
        else:
            logger.warning_rank0("`template` was not specified, use `empty` template.")
            template = TEMPLATES["empty"]  # placeholder
    else:
        if data_args.template not in TEMPLATES:
            raise ValueError(f"Template {data_args.template} does not exist.")

        template = TEMPLATES[data_args.template]

    if data_args.train_on_prompt and template.efficient_eos:
        raise ValueError("Current template does not support `train_on_prompt`.")

    if data_args.tool_format is not None:
        logger.info_rank0(f"Using tool format: {data_args.tool_format}.")
        default_slots = ["{{content}}"] if template.efficient_eos else ["{{content}}", {"eos_token"}]
        template.format_function = FunctionFormatter(slots=default_slots, tool_format=data_args.tool_format)
        template.format_tools = ToolFormatter(tool_format=data_args.tool_format)

    if data_args.default_system is not None:
        logger.info_rank0(f"Using default system message: {data_args.default_system}.")
        template.default_system = data_args.default_system

    if isinstance(template, ReasoningTemplate):
        logger.warning_rank0(
            "You are using reasoning template, "
            "please add `_nothink` suffix if the model is not a reasoning model. "
            "e.g., qwen3_vl_nothink"
        )
        template.enable_thinking = data_args.enable_thinking
        template.preserve_thinking = data_args.preserve_thinking

    template.fix_special_tokens(tokenizer)
    template.fix_jinja_template(tokenizer)
    return template