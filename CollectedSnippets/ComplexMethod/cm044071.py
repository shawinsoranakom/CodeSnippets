def set_parameter_options(  # noqa: PLR0912  # pylint: disable=too-many-branches
    p: dict, p_schema: dict, providers: list[str]
) -> dict:
    """
    Set options for the parameter based on the schema.

    Parameters
    ----------
    p : Dict
        Processed parameter dictionary.
    p_schema : Dict
        Schema dictionary for the parameter.
    providers : List[str]
        List of provider options.

    Returns
    -------
    Dict
        Updated parameter dictionary with options.
    """
    choices: dict[str, list[dict[str, str]]] = (
        p.get("options", {})
        if p.get("options")
        else p_schema.get("options", {}) if p_schema.get("options") else {}
    )
    widget_configs: dict[str, dict] = {}
    multiple_items_allowed_dict: dict = {}
    is_provider_specific = False
    available_providers: set = set()
    unique_general_choices: list = []
    provider: str = ""

    # Extract provider from title if present
    title_providers = []
    if (
        p_schema.get("title")
        and p_schema["title"] != p.get("parameter_name")
        and p_schema.get("title", "").islower()
    ):
        # Handle comma-separated providers in title field
        for title_name in p_schema["title"].lower().split(","):
            if title_name in [
                prov.lower() for prov in providers
            ]:  # Only actual providers
                title_providers.append(title_name)
                is_provider_specific = True
                available_providers.add(title_name)

    # Handle provider-specific choices
    for provider in providers:
        if provider in p_schema or (len(providers) == 1):
            is_provider_specific = True
            provider_choices: list = []
            if provider not in available_providers:
                available_providers.add(provider)
            if provider in p_schema:
                provider_choices = p_schema[provider].get("choices", [])
                if widget_def := p_schema[provider].get("x-widget_config"):
                    widget_configs[provider] = widget_def
            elif len(providers) == 1 and "enum" in p_schema:
                provider_choices = p_schema["enum"]
                p_schema.pop("enum")

            if provider_choices:
                choices[provider] = [
                    {"label": str(c), "value": c} for c in provider_choices
                ]
            if provider in p_schema and p_schema[provider].get(
                "multiple_items_allowed", False
            ):
                multiple_items_allowed_dict[provider] = True

    # Handle title provider choices if present
    if title_providers and "anyOf" in p_schema:
        # If we have multiple providers in title and multiple enum lists in anyOf
        # try to match them in order
        if (
            len(title_providers) > 1
            and len([s for s in p_schema["anyOf"] if "enum" in s]) > 1
        ):
            for i, provider in enumerate(title_providers):
                # Only process if this provider doesn't already have choices
                if provider not in choices or not choices[provider]:
                    # Try to match enum at the same position as the provider in the title
                    enum_index = min(i, len(p_schema["anyOf"]) - 1)
                    if "enum" in p_schema["anyOf"][enum_index]:
                        provider_choices = p_schema["anyOf"][enum_index]["enum"]
                        choices[provider] = [
                            {"label": str(c), "value": c}
                            for c in provider_choices
                            if c not in ["null", None]
                        ]
        else:
            # Existing code for single provider or multiple providers with one enum
            all_provider_choices = []
            for sub_schema in p_schema["anyOf"]:
                if "enum" in sub_schema:
                    all_provider_choices.extend(sub_schema["enum"])

            if all_provider_choices:
                for provider in title_providers:
                    if provider not in choices or not choices[provider]:
                        choices[provider] = [
                            {"label": str(c), "value": c}
                            for c in all_provider_choices
                            if c not in ["null", None]
                        ]

    # Check title for provider-specific information from description
    if p_schema.get("description") and "(provider:" in p_schema["description"]:
        desc_provider = (
            p_schema["description"].split("(provider:")[1].strip().rstrip(")")
        )
        if desc_provider and desc_provider not in available_providers:
            available_providers.add(desc_provider)
            is_provider_specific = True

    # Handle general choices
    general_choices: list = []
    if "enum" in p_schema:
        general_choices.extend(
            [
                {"label": str(c), "value": c}
                for c in p_schema["enum"]
                if c not in ["null", None]
            ]
        )
    elif "anyOf" in p_schema and not title_providers:
        for sub_schema in p_schema["anyOf"]:
            if "enum" in sub_schema:
                general_choices.extend(
                    [
                        {"label": str(c), "value": c}
                        for c in sub_schema["enum"]
                        if c not in ["null", None]
                    ]
                )

    if general_choices:
        # Remove duplicates by converting list of dicts to a set of tuples and back to list of dicts
        unique_general_choices = sorted(
            [dict(t) for t in {tuple(d.items()) for d in general_choices}],
            key=lambda x: x["label"],
        )
        if not is_provider_specific:
            if len(providers) == 1:
                choices[providers[0]] = unique_general_choices
                multiple_items_allowed_dict[providers[0]] = p_schema.get(
                    "multiple_items_allowed", False
                )
            else:
                choices["other"] = unique_general_choices
                multiple_items_allowed_dict["other"] = p_schema.get(
                    "multiple_items_allowed", False
                )

    # Use general choices as fallback for providers without specific options
    for provider in available_providers:
        if provider not in choices:
            if "anyOf" in p_schema and p_schema["anyOf"]:
                fallback_choices = p_schema["anyOf"][0].get("enum", [])
                choices[provider] = [
                    {"label": str(c), "value": c}
                    for c in fallback_choices
                    if c not in ["null", None]
                ]
            else:
                choices[provider] = unique_general_choices

        if provider in p_schema and p_schema[provider].get("x-widget_config"):
            widget_configs[provider] = p_schema[provider].get("x-widget_config")

    p["multiple_items_allowed"] = multiple_items_allowed_dict

    if choices:
        filtered_choices = {
            provider: choice for provider, choice in choices.items() if choice
        }
        p["options"] = (
            filtered_choices if filtered_choices else {provider: []} if provider else []
        )

    if is_provider_specific and len(available_providers) > 1:
        p["available_providers"] = list(available_providers)
        p["x-widget_config"] = widget_configs

    else:
        # Wrap single provider config under provider key for consistent handling
        single_config = widget_configs.get(provider, {}) if provider else widget_configs
        p["x-widget_config"] = (
            {provider: single_config} if provider and single_config else single_config
        )

    return p