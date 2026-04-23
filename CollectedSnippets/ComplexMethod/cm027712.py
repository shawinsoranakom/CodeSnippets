def validate_services(config: Config, integration: Integration) -> None:  # noqa: C901
    """Validate services."""
    try:
        data = load_yaml_dict(str(integration.path / "services.yaml"))
    except FileNotFoundError:
        # Find if integration uses services
        has_services = grep_dir(
            integration.path,
            "**/*.py",
            r"(hass\.services\.(register|async_register))|async_register_entity_service|async_register_admin_service",
        )

        if has_services:
            integration.add_error(
                "services", "Registers services but has no services.yaml"
            )
        return
    except HomeAssistantError:
        integration.add_error("services", "Invalid services.yaml")
        return

    try:
        if (
            integration.core
            and integration.domain not in VALIDATE_AS_CUSTOM_INTEGRATION
        ):
            services = CORE_INTEGRATION_SERVICES_SCHEMA(data)
        else:
            services = CUSTOM_INTEGRATION_SERVICES_SCHEMA(data)
    except vol.Invalid as err:
        integration.add_error(
            "services", f"Invalid services.yaml: {humanize_error(data, err)}"
        )
        return

    icons_file = integration.path / "icons.json"
    icons = {}
    if icons_file.is_file():
        with contextlib.suppress(ValueError):
            icons = json.loads(icons_file.read_text())
    service_icons = icons.get("services", {})

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

    # For each service in the integration:
    # 1. Check if the service description is set, if not,
    #    check if it's in the strings file else add an error.
    # 2. Check if the service has an icon set in icons.json.
    #    raise an error if not.,
    for service_name, service_schema in services.items():
        if integration.core and service_name not in service_icons:
            # This is enforced for Core integrations only
            integration.add_error(
                "services",
                f"Service {service_name} has no icon in icons.json.",
            )
        if service_schema is None:
            continue
        if "name" not in service_schema and integration.core:
            try:
                strings["services"][service_name]["name"]
            except KeyError:
                integration.add_error(
                    "services",
                    f"Service {service_name} has no name {error_msg_suffix}",
                )

        if "description" not in service_schema and integration.core:
            try:
                strings["services"][service_name]["description"]
            except KeyError:
                integration.add_error(
                    "services",
                    f"Service {service_name} has no description {error_msg_suffix}",
                )

        check_extraneous_translation_fields(
            integration, service_name, strings, service_schema
        )

        # The same check is done for each field in the service schema,
        # except that we don't require fields to have a description.
        for field_name, field_schema in service_schema.get("fields", {}).items():
            if "fields" in field_schema:
                # This is a section
                continue
            if "name" not in field_schema and integration.core:
                try:
                    strings["services"][service_name]["fields"][field_name]["name"]
                except KeyError:
                    integration.add_error(
                        "services",
                        f"Service {service_name} has a field {field_name} with no name {error_msg_suffix}",
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
                            "services",
                            f"Service {service_name} has a field {field_name} with a selector with a translation key {translation_key} that is not in the translations file",
                        )

        # The same check is done for the description in each of the sections of the
        # service schema.
        for section_name, section_schema in service_schema.get("fields", {}).items():
            if "fields" not in section_schema:
                # This is not a section
                continue
            if "name" not in section_schema and integration.core:
                try:
                    strings["services"][service_name]["sections"][section_name]["name"]
                except KeyError:
                    integration.add_error(
                        "services",
                        f"Service {service_name} has a section {section_name} with no name {error_msg_suffix}",
                    )