def _detect_providers_from_template(template: dict) -> set[str]:
    """Detect model providers from a component's template field values.

    Looks at model-selection fields (e.g., ``model``, ``agent_llm``) and
    extracts the ``provider`` string when the field is configured.
    """
    providers: set[str] = set()
    for field_name in _MODEL_FIELDS:
        field = template.get(field_name)
        if not isinstance(field, dict):
            continue
        value = field.get("value")
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "provider" in item:
                    providers.add(item["provider"])
        elif isinstance(value, dict) and "provider" in value:
            providers.add(value["provider"])
    return providers