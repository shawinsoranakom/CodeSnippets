def modify_query_schema(query_schema: list[dict], provider_value: str):
    """Modify query_schema and the description for the current provider."""
    # pylint: disable=import-outside-toplevel
    from .openapi import (
        TO_CAPS_STRINGS,
    )

    modified_query_schema: list = []
    if not query_schema:
        return modified_query_schema
    for item in query_schema:
        # copy the item
        _item = deepcopy(item)
        provider_value_options: dict = {}
        provider_value_widget_config: dict = {}
        # Exclude provider parameter. Those will be added last.
        if "parameter_name" in _item and _item["parameter_name"] == "provider":
            continue

        # Exclude parameters that are not available for the current provider.
        if (
            "available_providers" in _item
            and provider_value not in _item["available_providers"]
        ):
            continue

        if (
            provider_value
            and isinstance(_item, dict)
            and provider_value in _item.get("multiple_items_allowed", {})
            and _item.get("multiple_items_allowed", {}).get(provider_value, False)
        ):
            _item["description"] = (
                _item["description"] + " Multiple comma separated items allowed."
            )
            _item["type"] = "text"
            _item["multiSelect"] = True

        if "options" in _item and _item.get("options"):
            provider_value_options = _item.pop("options", None)
            if isinstance(provider_value_options, list):
                provider_value_options = {provider_value: provider_value_options}

        if provider_value in provider_value_options and bool(
            provider_value_options[provider_value]
        ):
            _item["options"] = provider_value_options[provider_value]
            _item["type"] = "text"
        elif len(provider_value_options) == 1 and "other" in provider_value_options:
            _item["options"] = provider_value_options["other"]
            _item["type"] = "text"

        _ = _item.pop("multiple_items_allowed", None)

        if "available_providers" in _item:
            _item.pop("available_providers")

        _item["paramName"] = _item.pop("parameter_name", None)

        if not _item.get("label") and _item["paramName"] in [
            "url",
            "cik",
            "lei",
            "cusip",
            "isin",
            "sedol",
        ]:
            _item["label"] = _item["paramName"].upper()

        if _label := _item.get("label"):
            _item["label"] = " ".join(
                [
                    (word.upper() if word in TO_CAPS_STRINGS else word)
                    for word in _label.split()
                ]
            )

        if xwidget := _item.pop("x-widget_config", {}):
            provider_value_widget_config[
                provider_value if provider_value else "custom"
            ] = xwidget.get(provider_value if provider_value else "custom", {})

        if (
            provider_value_widget_config
            and provider_value in provider_value_widget_config
        ):
            if provider_value_widget_config[provider_value].get("exclude"):
                continue

            if provider_value_widget_config[provider_value]:
                _item = deep_merge_configs(
                    _item,
                    provider_value_widget_config[provider_value],
                    ["paramName", "value"],
                )

        if not _item.get("label") and _item["paramName"] in [
            "url",
            "cik",
            "lei",
            "cusip",
            "isin",
            "sedol",
        ]:
            _item["label"] = _item["paramName"].upper()

        if _label := _item.get("label"):
            _item["label"] = " ".join(
                [
                    (word.upper() if word in TO_CAPS_STRINGS else word)
                    for word in _label.split()
                ]
            )

        if (
            _item.get("multiSelect") is True
            and _item.get("type") == "text"
            and not _item.get("options")
            and "semicolon" not in _item.get("description", "")
        ):
            _item["multiple"] = True
            _item["style"] = (
                _item.get("style", {}) if _item.get("style") else {"popupWidth": 400}
            )

        modified_query_schema.append(_item)

    if provider_value != "custom":
        modified_query_schema.append(
            {"paramName": "provider", "value": provider_value, "show": False}
        )

    return modified_query_schema