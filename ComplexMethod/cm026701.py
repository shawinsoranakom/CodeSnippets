def add_province_and_language_to_schema(
    schema: vol.Schema,
    country: str | None,
) -> vol.Schema:
    """Update schema with province from country."""
    if not country:
        return schema

    all_countries = list_supported_countries(include_aliases=False)

    language_schema = {}
    province_schema = {}

    _country = country_holidays(country=country)
    if country_default_language := (_country.default_language):
        new_selectable_languages = list(_country.supported_languages)
        language_schema = {
            vol.Optional(
                CONF_LANGUAGE, default=country_default_language
            ): LanguageSelector(
                LanguageSelectorConfig(
                    languages=new_selectable_languages, native_name=True
                )
            )
        }

    if provinces := all_countries.get(country):
        if _country.subdivisions_aliases and (
            subdiv_aliases := _country.get_subdivision_aliases()
        ):
            province_options: list[Any] = [
                SelectOptionDict(value=k, label=", ".join(v))
                for k, v in subdiv_aliases.items()
            ]
            for option in province_options:
                if option["label"] == "":
                    option["label"] = option["value"]
        else:
            province_options = provinces
        province_schema = {
            vol.Optional(CONF_PROVINCE): SelectSelector(
                SelectSelectorConfig(
                    options=province_options,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key=CONF_PROVINCE,
                )
            ),
        }

    category_schema = {}
    # PUBLIC will always be included and can therefore not be set/removed
    _categories = [x for x in _country.supported_categories if x != PUBLIC]
    if _categories:
        category_schema = {
            vol.Optional(CONF_CATEGORY): SelectSelector(
                SelectSelectorConfig(
                    options=_categories,
                    mode=SelectSelectorMode.DROPDOWN,
                    multiple=True,
                    translation_key=CONF_CATEGORY,
                )
            ),
        }

    return vol.Schema(
        {
            **DATA_SCHEMA_OPT.schema,
            **language_schema,
            **province_schema,
            **category_schema,
        }
    )