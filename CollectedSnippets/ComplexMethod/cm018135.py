async def _validate_translation(
    hass: HomeAssistant,
    translation_errors: dict[str, str],
    ignore_translations_for_mock_domains: set[str],
    category: str,
    component: str,
    key: str,
    description_placeholders: Mapping[str, str] | None,
    *,
    translation_required: bool = True,
) -> None:
    """Raise if translation doesn't exist."""
    full_key = f"component.{component}.{category}.{key}"
    if component in ignore_translations_for_mock_domains:
        try:
            integration = await loader.async_get_integration(hass, component)
        except loader.IntegrationNotFound:
            return
        component_paths = components.__path__
        if not any(
            Path(f"{component_path}/{component}") == integration.file_path
            for component_path in component_paths
        ):
            return
        # If the integration exists, translation errors should be ignored via the
        # ignore_missing_translations fixture instead of the
        # ignore_translations_for_mock_domains fixture.
        translation_errors[full_key] = f"The integration '{component}' exists"
        return

    translations = await async_get_translations(hass, "en", category, [component])

    if full_key.endswith("."):
        for subkey, translation in translations.items():
            if subkey.startswith(full_key):
                _validate_translation_placeholders(
                    subkey, translation, description_placeholders, translation_errors
                )
        return
    if (translation := translations.get(full_key)) is not None:
        _validate_translation_placeholders(
            full_key, translation, description_placeholders, translation_errors
        )
        return

    if not translation_required:
        return

    if full_key not in translation_errors:
        for k in translation_errors:
            if k.endswith(".") and full_key.startswith(k):
                full_key = k
                break
    if translation_errors.get(full_key) in {"used", "unused"}:
        # If the integration does not exist, translation errors should be ignored
        # via the ignore_translations_for_mock_domains fixture instead of the
        # ignore_missing_translations fixture.
        try:
            await loader.async_get_integration(hass, component)
        except loader.IntegrationNotFound:
            translation_errors[full_key] = (
                f"Translation not found for {component}: `{category}.{key}`. "
                f"The integration '{component}' does not exist."
            )
            return

        # This translation key is in the ignore list, mark it as used
        translation_errors[full_key] = "used"
        return

    translation_errors[full_key] = (
        f"Translation not found for {component}: `{category}.{key}`. "
        f"Please add to homeassistant/components/{component}/strings.json"
    )