def _create_prompt_definitions_for_route(
    route: APIRoute, settings: MCPSettings | None = None
) -> list[dict]:
    """Create prompt definitions for a route if prompt configs exist."""
    prompt_configs = _get_prompt_configs(route)
    definitions: list[dict] = []

    if not prompt_configs:
        return definitions

    # Get argument definitions from the endpoint's signature
    # This provides the ground truth for parameter names, types, and defaults
    try:
        sig = inspect.signature(route.endpoint)
        endpoint_args = {
            p.name: {
                "name": p.name,
                "type": (
                    p.annotation.__name__
                    if hasattr(p.annotation, "__name__")
                    else "str"
                ),
                "default": p.default if p.default is not p.empty else ...,
            }
            for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
        }
    except (ValueError, TypeError):
        # Cannot inspect signature
        endpoint_args = {}

    # Common info for all prompts on this route
    api_prefix = get_api_prefix(settings)
    tool_uri = route.path.replace(api_prefix, "").lstrip("/").replace("/", "_")
    path = route.path or ""
    if not path.startswith("/"):
        path = "/" + path
    remainder = (
        path[len(api_prefix) :] if api_prefix and path.startswith(api_prefix) else path
    )
    local_path = remainder.lstrip("/")
    segments = [seg for seg in local_path.split("/") if seg and "{" not in seg]

    if segments:
        category = segments[0]
        if len(segments) == 1:
            subcategory = "general"
            tool = segments[0]
        elif len(segments) == 2:
            subcategory = "general"
            tool = segments[1]
        else:
            subcategory = segments[1]
            tool = "_".join(segments[2:])
    else:
        category, subcategory, tool = "general", "general", "root"

    for i, prompt_cfg in enumerate(prompt_configs):
        if not prompt_cfg or not prompt_cfg.get("content"):
            continue

        # Generate prompt name
        prompt_name = prompt_cfg.get("name")
        if not prompt_name:
            base_name = (
                f"{category}_{subcategory}_{tool}"
                if subcategory != "general"
                else f"{category}_{tool}"
            )
            # Add index for uniqueness if multiple unnamed prompts exist
            suffix = f"_{i}" if len(prompt_configs) > 1 else ""
            prompt_name = f"{base_name}_prompt{suffix}"

        # Arguments for the prompt can be a combination of endpoint args and custom ones
        final_args: dict = {}
        prompt_arg_defs = {arg["name"]: arg for arg in prompt_cfg.get("arguments", [])}
        content = (
            f"Use the tool, {tool_uri}, to perform the following task.\n\n"
            + prompt_cfg.get("content", "")
        )

        # All variables in the content string are considered arguments for the prompt
        prompt_vars = re.findall(r"\{(\w+)\}", content)

        for var in set(prompt_vars):
            if var in prompt_arg_defs:
                # Use the definition from the prompt's own 'arguments' list
                final_args[var] = prompt_arg_defs[var]
            elif var in endpoint_args:
                # Inherit the definition from the endpoint's signature
                final_args[var] = endpoint_args[var]
            else:
                # Argument is required by prompt but not defined anywhere
                final_args[var] = {"name": var, "type": "str"}

        # Build prompt definition
        prompt_def = {
            "name": prompt_name,
            "description": prompt_cfg.get("description") or f"Prompt for {tool_uri}",
            "content": content,
            "arguments": list(final_args.values()),
            "tool": tool_uri,
        }

        # Add tags, always including the route path
        tags = list(prompt_cfg.get("tags", []))
        if route.path and route.path not in tags:
            tags.insert(0, route.path)
        prompt_def["tags"] = tags

        definitions.append(prompt_def)

    return definitions