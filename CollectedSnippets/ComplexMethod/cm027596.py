async def _async_get_component_strings(
    hass: HomeAssistant,
    languages: Iterable[str],
    components: set[str],
    integrations: dict[str, Integration],
) -> dict[str, dict[str, Any]]:
    """Load translations."""
    translations_by_language: dict[str, dict[str, Any]] = {}
    # Determine paths of missing components/platforms
    files_to_load_by_language: dict[str, dict[str, pathlib.Path]] = {}
    loaded_translations_by_language: dict[str, dict[str, Any]] = {}
    has_files_to_load = False
    for language in languages:
        file_name = f"{language}.json"
        files_to_load: dict[str, pathlib.Path] = {
            domain: integration.file_path / "translations" / file_name
            for domain in components
            if (
                (integration := integrations.get(domain))
                and integration.has_translations
            )
        }
        files_to_load_by_language[language] = files_to_load
        has_files_to_load |= bool(files_to_load)

    if has_files_to_load:
        loaded_translations_by_language = await hass.async_add_executor_job(
            _load_translations_files_by_language, files_to_load_by_language
        )

    for language in languages:
        loaded_translations = loaded_translations_by_language.setdefault(language, {})
        for domain in components:
            # Translations that miss "title" will get integration put in.
            component_translations = loaded_translations.setdefault(domain, {})
            if "title" not in component_translations and (
                integration := integrations.get(domain)
            ):
                component_translations["title"] = integration.name

        translations_by_language.setdefault(language, {}).update(loaded_translations)

    return translations_by_language