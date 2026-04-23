def validate_triggers(config: Config, integration: Integration) -> None:  # noqa: C901
    """Validate triggers."""
    try:
        data = load_yaml_dict(str(integration.path / "triggers.yaml"))
    except FileNotFoundError:
        # Find if integration uses triggers
        has_triggers = grep_dir(
            integration.path,
            "**/trigger.py",
            r"async_attach_trigger|async_get_triggers",
        )

        if has_triggers and integration.domain not in NON_MIGRATED_INTEGRATIONS:
            integration.add_error(
                "triggers", "Registers triggers but has no triggers.yaml"
            )
        return
    except HomeAssistantError:
        integration.add_error("triggers", "Invalid triggers.yaml")
        return

    try:
        triggers = TRIGGERS_SCHEMA(data)
    except vol.Invalid as err:
        integration.add_error(
            "triggers", f"Invalid triggers.yaml: {humanize_error(data, err)}"
        )
        return

    icons_file = integration.path / "icons.json"
    icons = {}
    if icons_file.is_file():
        with contextlib.suppress(ValueError):
            icons = json.loads(icons_file.read_text())
    trigger_icons = icons.get("triggers", {})

    # Try loading translation strings
    if integration.core:
        strings_file = integration.path / "strings.json"
    else:
        # For custom integrations, use the en.json file
        strings_file = integration.path / "translations/en.json"

    strings = {}
    if strings_file.is_file():
        with contextlib.suppress(ValueError):
            strings = json.loads(strings_file.read_text())

    error_msg_suffix = "in the translations file"
    if not integration.core:
        error_msg_suffix = f"and is not {error_msg_suffix}"

    # For each trigger in the integration:
    # 1. Check if the trigger description is set, if not,
    #    check if it's in the strings file else add an error.
    # 2. Check if the trigger has an icon set in icons.json.
    #    raise an error if not.,
    for trigger_name, trigger_schema in triggers.items():
        if integration.core and trigger_name not in trigger_icons:
            # This is enforced for Core integrations only
            integration.add_error(
                "triggers",
                f"Trigger {trigger_name} has no icon in icons.json.",
            )
        if trigger_schema is None:
            continue
        if "name" not in trigger_schema and integration.core:
            try:
                strings["triggers"][trigger_name]["name"]
            except KeyError:
                integration.add_error(
                    "triggers",
                    f"Trigger {trigger_name} has no name {error_msg_suffix}",
                )

        if "description" not in trigger_schema and integration.core:
            try:
                strings["triggers"][trigger_name]["description"]
            except KeyError:
                integration.add_error(
                    "triggers",
                    f"Trigger {trigger_name} has no description {error_msg_suffix}",
                )

        # The same check is done for each of the fields of the trigger schema,
        # except that we don't enforce that fields have a description.
        for field_name, field_schema in trigger_schema.get("fields", {}).items():
            if "fields" in field_schema:
                # This is a section
                continue
            if "name" not in field_schema and integration.core:
                try:
                    strings["triggers"][trigger_name]["fields"][field_name]["name"]
                except KeyError:
                    integration.add_error(
                        "triggers",
                        (
                            f"Trigger {trigger_name} has a field {field_name} with no "
                            f"name {error_msg_suffix}"
                        ),
                    )

            if "selector" in field_schema:
                with contextlib.suppress(KeyError):
                    translation_key = field_schema["selector"]["select"][
                        "translation_key"
                    ]
                    try:
                        strings["selector"][translation_key]
                    except KeyError:
                        integration.add_error(
                            "triggers",
                            f"Trigger {trigger_name} has a field {field_name} with a selector with a translation key {translation_key} that is not in the translations file",
                        )

        # The same check is done for the description in each of the sections of the
        # trigger schema.
        for section_name, section_schema in trigger_schema.get("fields", {}).items():
            if "fields" not in section_schema:
                # This is not a section
                continue
            if "name" not in section_schema and integration.core:
                try:
                    strings["triggers"][trigger_name]["sections"][section_name]["name"]
                except KeyError:
                    integration.add_error(
                        "triggers",
                        f"Trigger {trigger_name} has a section {section_name} with no name {error_msg_suffix}",
                    )