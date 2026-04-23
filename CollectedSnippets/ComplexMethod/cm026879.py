def websocket_list_languages(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List languages which are supported by a complete pipeline.

    This will return a list of languages which are supported by at least one stt, tts
    and conversation engine respectively.
    """
    conv_language_tags = conversation.async_get_conversation_languages(hass)
    stt_language_tags = stt.async_get_speech_to_text_languages(hass)
    tts_language_tags = tts.async_get_text_to_speech_languages(hass)
    pipeline_languages: set[str] | None = None

    if conv_language_tags and conv_language_tags != MATCH_ALL:
        languages = set()
        for language_tag in conv_language_tags:
            dialect = language_util.Dialect.parse(language_tag)
            languages.add(dialect.language)
        pipeline_languages = languages

    if stt_language_tags:
        languages = set()
        for language_tag in stt_language_tags:
            dialect = language_util.Dialect.parse(language_tag)
            languages.add(dialect.language)
        if pipeline_languages is not None:
            pipeline_languages = language_util.intersect(pipeline_languages, languages)
        else:
            pipeline_languages = languages

    if tts_language_tags:
        languages = set()
        for language_tag in tts_language_tags:
            dialect = language_util.Dialect.parse(language_tag)
            languages.add(dialect.language)
        if pipeline_languages is not None:
            pipeline_languages = language_util.intersect(pipeline_languages, languages)
        else:
            pipeline_languages = languages

    connection.send_result(
        msg["id"],
        {
            "languages": (
                sorted(pipeline_languages) if pipeline_languages else pipeline_languages
            )
        },
    )