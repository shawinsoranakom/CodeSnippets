def _add_prompts_from_json(mcp: FastMCP, settings: MCPSettings) -> None:
    """Load prompts from server_prompts_file and register them with mcp."""
    if not settings.server_prompts_file:
        return

    try:
        with open(settings.server_prompts_file, encoding="utf-8") as f:
            prompts_json: list = json.load(f) or []
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to load prompts from JSON file: %s", e)
        return

    prompts_added: list = []
    for prompt_def in prompts_json:
        prompt_name = prompt_def.get("name", "")

        if not prompt_name:
            logger.error("Skipping prompt definition without a name: %s", prompt_def)
            continue

        prompt_description = prompt_def.get("description", "")

        if not prompt_description:
            logger.error(
                "Skipping prompt definition without a description: %s", prompt_def
            )
            continue

        prompt_content = prompt_def.get("content", "")

        if not prompt_content:
            logger.error("Skipping prompt definition without content: %s", prompt_def)
            continue

        if not isinstance(prompt_content, str):
            logger.error(
                "Skipping prompt definition with invalid content type. Expected string, got: %s",
                prompt_def,
            )
            continue

        prompt_arguments_def = prompt_def.get("arguments", [])
        arguments: list = []

        argument_defaults: dict = {}

        if prompt_arguments_def:
            for arg in prompt_arguments_def:
                try:
                    validated_arg = ArgumentDefinitionModel(**arg).model_dump(
                        exclude_none=True
                    )
                    arguments.append(
                        PromptArgument(
                            name=validated_arg["name"],
                            description=validated_arg["description"],
                            required="default" not in validated_arg,
                        )
                    )
                    if "default" in validated_arg:
                        argument_defaults[validated_arg["name"]] = validated_arg[
                            "default"
                        ]
                except Exception as e:  # pylint: disable=broad-except
                    logger.error(
                        "Skipping argument definition in server prompt, %s, due to error: %s\nDefinition: %s",
                        prompt_name,
                        e,
                        arg,
                    )
                    continue

        prompt_tags = prompt_def.get("tags", [])
        tags = set(prompt_tags) if isinstance(prompt_tags, list | set) else set()
        tags.add("server")
        mcp.add_prompt(
            StaticPrompt(
                name=prompt_name,
                description=prompt_description,
                content=prompt_content,
                arguments=arguments if arguments else None,
                argument_defaults=argument_defaults,
                tags=tags,
            )
        )
        prompts_added.append(prompt_name)

    logger.info("Successfully added %d server prompts.", len(prompts_added))