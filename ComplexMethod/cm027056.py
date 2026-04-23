async def generate_content(call: ServiceCall) -> ServiceResponse:
        """Generate content from text and optionally images."""
        LOGGER.warning(
            "Action '%s.%s' is deprecated and will be removed in the 2026.4.0 release. "
            "Please use the 'ai_task.generate_data' action instead",
            DOMAIN,
            SERVICE_GENERATE_CONTENT,
        )
        ir.async_create_issue(
            hass,
            DOMAIN,
            "deprecated_generate_content",
            breaks_in_ha_version="2026.4.0",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="deprecated_generate_content",
        )

        prompt_parts = [call.data[CONF_PROMPT]]

        config_entry: GoogleGenerativeAIConfigEntry = (
            hass.config_entries.async_loaded_entries(DOMAIN)[0]
        )

        client = config_entry.runtime_data

        files = call.data[CONF_FILENAMES]

        if files:
            for filename in files:
                if not hass.config.is_allowed_path(filename):
                    raise HomeAssistantError(
                        f"Cannot read `{filename}`, no access to path; "
                        "`allowlist_external_dirs` may need to be adjusted in "
                        "`configuration.yaml`"
                    )

            prompt_parts.extend(
                await async_prepare_files_for_prompt(
                    hass, client, [(Path(filename), None) for filename in files]
                )
            )

        try:
            response = await client.aio.models.generate_content(
                model=RECOMMENDED_CHAT_MODEL, contents=prompt_parts
            )
        except (
            APIError,
            ValueError,
        ) as err:
            raise HomeAssistantError(f"Error generating content: {err}") from err

        if response.prompt_feedback:
            raise HomeAssistantError(
                f"Error generating content due to content violations, reason: {response.prompt_feedback.block_reason_message}"
            )

        if (
            not response.candidates
            or not response.candidates[0].content
            or not response.candidates[0].content.parts
        ):
            raise HomeAssistantError("Unknown error generating content")

        return {"text": response.text}