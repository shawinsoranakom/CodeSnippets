async def google_generative_ai_config_option_schema(
    hass: HomeAssistant,
    is_new: bool,
    subentry_type: str,
    options: Mapping[str, Any],
    genai_client: genai.Client,
) -> dict:
    """Return a schema for Google Generative AI completion options."""
    hass_apis: list[SelectOptionDict] = [
        SelectOptionDict(
            label=api.name,
            value=api.id,
        )
        for api in llm.async_get_apis(hass)
    ]
    if suggested_llm_apis := options.get(CONF_LLM_HASS_API):
        if isinstance(suggested_llm_apis, str):
            suggested_llm_apis = [suggested_llm_apis]
        known_apis = {api.id for api in llm.async_get_apis(hass)}
        suggested_llm_apis = [api for api in suggested_llm_apis if api in known_apis]

    if is_new:
        if CONF_NAME in options:
            default_name = options[CONF_NAME]
        elif subentry_type == "tts":
            default_name = DEFAULT_TTS_NAME
        elif subentry_type == "ai_task_data":
            default_name = DEFAULT_AI_TASK_NAME
        elif subentry_type == "stt":
            default_name = DEFAULT_STT_NAME
        else:
            default_name = DEFAULT_CONVERSATION_NAME
        schema: dict[vol.Required | vol.Optional, Any] = {
            vol.Required(CONF_NAME, default=default_name): str,
        }
    else:
        schema = {}

    if subentry_type == "conversation":
        schema.update(
            {
                vol.Optional(
                    CONF_PROMPT,
                    description={
                        "suggested_value": options.get(
                            CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT
                        )
                    },
                ): TemplateSelector(),
                vol.Optional(
                    CONF_LLM_HASS_API,
                    description={"suggested_value": suggested_llm_apis},
                ): SelectSelector(
                    SelectSelectorConfig(options=hass_apis, multiple=True)
                ),
            }
        )
    elif subentry_type == "stt":
        schema.update(
            {
                vol.Optional(
                    CONF_PROMPT,
                    description={
                        "suggested_value": options.get(CONF_PROMPT, DEFAULT_STT_PROMPT)
                    },
                ): TemplateSelector(),
            }
        )

    schema.update(
        {
            vol.Required(
                CONF_RECOMMENDED, default=options.get(CONF_RECOMMENDED, False)
            ): bool,
        }
    )

    if options.get(CONF_RECOMMENDED):
        return schema

    api_models_pager = await genai_client.aio.models.list(config={"query_base": True})
    api_models = [api_model async for api_model in api_models_pager]
    models = [
        SelectOptionDict(
            label=api_model.name.lstrip("models/"),
            value=api_model.name,
        )
        for api_model in sorted(
            api_models, key=lambda x: (x.name or "").lstrip("models/")
        )
        if (
            api_model.name
            and ("tts" in api_model.name) == (subentry_type == "tts")
            and "vision" not in api_model.name
            and api_model.supported_actions
            and "generateContent" in api_model.supported_actions
        )
    ]

    harm_block_thresholds: list[SelectOptionDict] = [
        SelectOptionDict(
            label="Block none",
            value="BLOCK_NONE",
        ),
        SelectOptionDict(
            label="Block few",
            value="BLOCK_ONLY_HIGH",
        ),
        SelectOptionDict(
            label="Block some",
            value="BLOCK_MEDIUM_AND_ABOVE",
        ),
        SelectOptionDict(
            label="Block most",
            value="BLOCK_LOW_AND_ABOVE",
        ),
    ]
    harm_block_thresholds_selector = SelectSelector(
        SelectSelectorConfig(
            mode=SelectSelectorMode.DROPDOWN, options=harm_block_thresholds
        )
    )

    if subentry_type == "tts":
        default_model = RECOMMENDED_TTS_MODEL
    elif subentry_type == "stt":
        default_model = RECOMMENDED_STT_MODEL
    else:
        default_model = RECOMMENDED_CHAT_MODEL

    schema.update(
        {
            vol.Optional(
                CONF_CHAT_MODEL,
                description={"suggested_value": options.get(CONF_CHAT_MODEL)},
                default=default_model,
            ): SelectSelector(
                SelectSelectorConfig(mode=SelectSelectorMode.DROPDOWN, options=models)
            ),
            vol.Optional(
                CONF_TEMPERATURE,
                description={"suggested_value": options.get(CONF_TEMPERATURE)},
                default=RECOMMENDED_TEMPERATURE,
            ): NumberSelector(NumberSelectorConfig(min=0, max=2, step=0.05)),
            vol.Optional(
                CONF_TOP_P,
                description={"suggested_value": options.get(CONF_TOP_P)},
                default=RECOMMENDED_TOP_P,
            ): NumberSelector(NumberSelectorConfig(min=0, max=1, step=0.05)),
            vol.Optional(
                CONF_TOP_K,
                description={"suggested_value": options.get(CONF_TOP_K)},
                default=RECOMMENDED_TOP_K,
            ): int,
            vol.Optional(
                CONF_MAX_TOKENS,
                description={"suggested_value": options.get(CONF_MAX_TOKENS)},
                default=RECOMMENDED_MAX_TOKENS,
            ): int,
            vol.Optional(
                CONF_HARASSMENT_BLOCK_THRESHOLD,
                description={
                    "suggested_value": options.get(CONF_HARASSMENT_BLOCK_THRESHOLD)
                },
                default=RECOMMENDED_HARM_BLOCK_THRESHOLD,
            ): harm_block_thresholds_selector,
            vol.Optional(
                CONF_HATE_BLOCK_THRESHOLD,
                description={"suggested_value": options.get(CONF_HATE_BLOCK_THRESHOLD)},
                default=RECOMMENDED_HARM_BLOCK_THRESHOLD,
            ): harm_block_thresholds_selector,
            vol.Optional(
                CONF_SEXUAL_BLOCK_THRESHOLD,
                description={
                    "suggested_value": options.get(CONF_SEXUAL_BLOCK_THRESHOLD)
                },
                default=RECOMMENDED_HARM_BLOCK_THRESHOLD,
            ): harm_block_thresholds_selector,
            vol.Optional(
                CONF_DANGEROUS_BLOCK_THRESHOLD,
                description={
                    "suggested_value": options.get(CONF_DANGEROUS_BLOCK_THRESHOLD)
                },
                default=RECOMMENDED_HARM_BLOCK_THRESHOLD,
            ): harm_block_thresholds_selector,
        }
    )
    if subentry_type == "conversation":
        schema.update(
            {
                vol.Optional(
                    CONF_USE_GOOGLE_SEARCH_TOOL,
                    description={
                        "suggested_value": options.get(CONF_USE_GOOGLE_SEARCH_TOOL),
                    },
                    default=RECOMMENDED_USE_GOOGLE_SEARCH_TOOL,
                ): bool,
            }
        )

    return schema