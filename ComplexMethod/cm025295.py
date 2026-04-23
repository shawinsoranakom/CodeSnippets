async def send_prompt(call: ServiceCall) -> ServiceResponse:
        """Send a prompt to ChatGPT and return the response."""
        LOGGER.warning(
            "Action '%s.%s' is deprecated and will be removed in the 2026.9.0 release. "
            "Please use the 'ai_task.generate_data' action instead",
            DOMAIN,
            SERVICE_GENERATE_CONTENT,
        )
        ir.async_create_issue(
            hass,
            DOMAIN,
            "deprecated_generate_content",
            breaks_in_ha_version="2026.9.0",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="deprecated_generate_content",
        )

        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)

        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_config_entry",
                translation_placeholders={"config_entry": entry_id},
            )

        # Get first conversation subentry for options
        conversation_subentry = next(
            (
                sub
                for sub in entry.subentries.values()
                if sub.subentry_type == "conversation"
            ),
            None,
        )
        if not conversation_subentry:
            raise ServiceValidationError("No conversation configuration found")

        model: str = conversation_subentry.data.get(
            CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL
        )
        client: openai.AsyncClient = entry.runtime_data

        content: ResponseInputMessageContentListParam = [
            ResponseInputTextParam(type="input_text", text=call.data[CONF_PROMPT])
        ]

        if filenames := call.data.get(CONF_FILENAMES):
            for filename in filenames:
                if not hass.config.is_allowed_path(filename):
                    raise HomeAssistantError(
                        f"Cannot read `{filename}`, no access to path; "
                        "`allowlist_external_dirs` may need to be adjusted in "
                        "`configuration.yaml`"
                    )

            content.extend(
                await async_prepare_files_for_prompt(
                    hass, [(Path(filename), None) for filename in filenames]
                )
            )

        messages: ResponseInputParam = [
            EasyInputMessageParam(type="message", role="user", content=content)
        ]

        model_args = {
            "model": model,
            "input": messages,
            "max_output_tokens": conversation_subentry.data.get(
                CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS
            ),
            "top_p": conversation_subentry.data.get(CONF_TOP_P, RECOMMENDED_TOP_P),
            "temperature": conversation_subentry.data.get(
                CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE
            ),
            "user": call.context.user_id,
            "store": conversation_subentry.data.get(
                CONF_STORE_RESPONSES, RECOMMENDED_STORE_RESPONSES
            ),
        }

        if model.startswith("o"):
            model_args["reasoning"] = {
                "effort": conversation_subentry.data.get(
                    CONF_REASONING_EFFORT, RECOMMENDED_REASONING_EFFORT
                )
            }

        try:
            response: Response = await client.responses.create(**model_args)
        except openai.AuthenticationError as err:
            entry.async_start_reauth(hass)
            raise HomeAssistantError("Authentication error") from err
        except openai.OpenAIError as err:
            raise HomeAssistantError(f"Error generating content: {err}") from err
        except FileNotFoundError as err:
            raise HomeAssistantError(f"Error generating content: {err}") from err

        return {"text": response.output_text}