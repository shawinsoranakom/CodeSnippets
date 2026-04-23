def validate_translation_file(
    config: Config,
    integration: Integration,
    all_strings: dict[str, Any] | None,
) -> None:
    """Validate translation files for integration."""
    if config.specific_integrations:
        check_translations_directory_name(integration)

    strings_files = [integration.path / "strings.json"]

    # Also validate translations for custom integrations
    if config.specific_integrations:
        # Only English needs to be always complete
        strings_files.append(integration.path / "translations/en.json")

    references: list[dict[str, str]] = []

    if integration.domain == "auth":
        strings_schema = gen_auth_schema(config, integration)
    elif integration.domain == "onboarding":
        strings_schema = ONBOARDING_SCHEMA
    elif integration.domain == "homeassistant_hardware":
        strings_schema = gen_ha_hardware_schema(config, integration)
    else:
        strings_schema = gen_strings_schema(config, integration)

    for strings_file in strings_files:
        if not strings_file.is_file():
            continue

        name = str(strings_file.relative_to(integration.path))

        try:
            strings = json.loads(strings_file.read_text())
        except ValueError as err:
            integration.add_error("translations", f"Invalid JSON in {name}: {err}")
            continue

        try:
            strings_schema(strings)
        except vol.Invalid as err:
            integration.add_error(
                "translations", f"Invalid {name}: {humanize_error(strings, err)}"
            )
        else:
            if strings_file.name == "strings.json":
                find_references(strings, name, references)

                if (title := strings.get("title")) is not None:
                    integration.translated_name = True
                    if title == integration.name and not allow_name_translation(
                        integration
                    ):
                        integration.add_error(
                            "translations",
                            "Don't specify title in translation strings if it's "
                            "a brand name or add exception to ALLOW_NAME_TRANSLATION",
                        )

    if config.specific_integrations:
        return

    if not all_strings:  # Nothing to validate against
        return

    # Validate references
    for reference in references:
        parts = reference["ref"].split("::")
        search = all_strings
        key = parts.pop(0)
        while parts and key in search:
            search = search[key]
            key = parts.pop(0)

        if parts or key not in search:
            integration.add_error(
                "translations",
                f"{reference['source']} contains invalid reference"
                f"{reference['ref']}: Could not find {key}",
            )
        elif match := re.match(RE_REFERENCE, search[key]):
            integration.add_error(
                "translations",
                "Lokalise supports only one level of references: "
                f'"{reference["source"]}" should point to directly '
                f'to "{match.group(1)}"',
            )