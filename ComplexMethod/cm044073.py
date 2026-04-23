def process_parameter(
    param: dict, providers: list[str], single_provider: str | None = None
) -> dict:
    """Process a single parameter and return the processed dictionary.

    Parameters
    ----------
    param : dict
        The parameter definition from OpenAPI spec.
    providers : list[str]
        List of all available providers.
    single_provider : str | None
        If set, extract description/default only for this provider.

    Returns
    -------
    dict
        Processed parameter dictionary.
    """
    p: dict = {}
    schema = param.get("schema", {})

    param_name = param["name"]
    p["parameter_name"] = param_name
    p["label"] = (
        param_name.replace("_", " ").replace("fixedincome", "fixed income").title()
    )

    if not p.get("label") or p.get("label") == "":
        p["label"] = schema.get("title") or param.get("title")

    # Extract provider-specific description if single_provider is specified
    if single_provider and param.get("description"):
        p["description"] = _extract_provider_description(
            param.get("description", param_name), single_provider
        )
    else:
        p["description"] = (
            (param.get("description", param_name).split(" (provider:")[0].strip())
            .split("Multiple comma separated items allowed")[0]
            .strip()
            if param.get("description")
            else (schema.get("description") or p.get("label"))
        )
    p["optional"] = param.get("required", False) is False

    # Set type first so we can use it for value determination
    p["type"] = param.get("type", "text")

    # Get default value from schema if present
    # When single_provider is set, only use default if it belongs to that provider
    default_value = None

    if single_provider:
        # Check if this provider has a specific default in the schema
        provider_schema = schema.get(single_provider, {})
        if isinstance(provider_schema, dict) and "default" in provider_schema:
            default_value = provider_schema["default"]
        else:
            # Check if any other provider has a specific default that differs
            # If so, don't use the global default for this provider
            other_provider_defaults = [
                schema.get(prov, {}).get("default")
                for prov in providers
                if prov != single_provider
                and isinstance(schema.get(prov), dict)
                and "default" in schema.get(prov, {})
            ]
            # If other providers have specific defaults, don't use global default
            # Otherwise, fall back to global default
            if not other_provider_defaults:
                default_value = param.get("default") or schema.get("default")
    else:
        default_value = param.get("default")
        if default_value is None:
            default_value = schema.get("default")

    p["value"] = default_value if default_value is not None else param.get("value")

    # Special handling for provider parameter
    if param_name == "provider":
        p["type"] = "text"
        p["label"] = "Provider"
        p["description"] = "Source of the data."
        p["show"] = False
        p["available_providers"] = providers
        p["value"] = None
        return p

    multiple_items_allowed_dict: dict = {}
    for _provider in providers:
        if param.get("schema", {}).get(_provider, {}).get(
            "multiple_items_allowed"
        ) and param["schema"][_provider].get("multiple_items_allowed"):
            multiple_items_allowed_dict[_provider] = True

    p["multiple_items_allowed"] = multiple_items_allowed_dict

    # Safe check for description
    if (
        p.get("description", "")
        and "Multiple comma separated items allowed" in p["description"]  # type: ignore
    ):
        p["description"] = (
            p["description"].split("Multiple comma separated items allowed")[0].strip()  # type: ignore
        )

    if x_widget_config := param.get(
        "x-widget_config", param.get("schema", {}).get("x-widget_config", {})
    ):
        p["x-widget_config"] = x_widget_config

    p_schema = param.get("schema", {}) or param

    # Initialize provider specificity tracking
    provider_specific = False
    available_providers_list = (
        []
    )  # Start with empty list - only add providers that match

    # Extract providers from title
    if p_schema.get("title"):
        # Handle comma-separated list of providers in the title
        if "," in p_schema["title"]:
            title_providers = [p.strip().lower() for p in p_schema["title"].split(",")]
            available_providers_list.extend(title_providers)
            provider_specific = True
        elif p_schema["title"].lower() in [p.lower() for p in providers]:
            # Single provider in title
            available_providers_list.append(p_schema["title"].lower())
            provider_specific = True

    # Extract providers from description
    description = param.get("description", "")
    if description and "(provider:" in description:
        desc_parts = description.split("(provider:")
        for part in desc_parts[1:]:  # Skip the first part (before any provider mention)
            desc_provider_text = part.split(")")[0].strip()
            # Handle multiple providers separated by commas in description
            for dp in desc_provider_text.split(","):
                desc_provider = dp.strip().lower()
                if desc_provider and desc_provider not in available_providers_list:
                    available_providers_list.append(desc_provider)
                    provider_specific = True

    # Process options and types
    p = set_parameter_options(p, p_schema, providers)
    p = set_parameter_type(p, p_schema)

    # Ensure options has the expected format: {"provider": []} rather than just []
    if "options" not in p:
        p["options"] = {} if providers else []
        if providers:
            for provider in providers:
                p["options"][provider] = []  # type: ignore

    # Handle widget config
    if _widget_config := p_schema.get("x-widget_config", {}):
        for provider in providers:
            if provider in _widget_config:
                _widget_config = _widget_config[provider]
                break
        p.update(_widget_config)

    # Check if this parameter is provider-specific and filter appropriately
    if provider_specific and available_providers_list:
        # ONLY include providers that are actually in the provided providers list
        valid_provider_list = [
            p
            for p in available_providers_list
            if p.lower() in [prov.lower() for prov in providers]
        ]

        if valid_provider_list:
            # If set_parameter_options already determined a broader
            # available_providers list (by inspecting actual schema entries),
            # prefer that over the narrower title/description-based list.
            existing_providers = p.get("available_providers")
            if not existing_providers or len(valid_provider_list) > len(
                existing_providers
            ):
                p["available_providers"] = valid_provider_list

            effective_providers = p["available_providers"]
            # Check if any of our current providers match the available providers list
            valid_for_current_providers = any(
                current_provider.lower()
                in [valid_p.lower() for valid_p in effective_providers]
                for current_provider in providers
            )

            # If parameter is provider-specific but not valid for any of our current providers, skip it
            if not valid_for_current_providers:
                return {}

    return p