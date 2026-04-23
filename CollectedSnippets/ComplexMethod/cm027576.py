def _async_get_tools(
        self, llm_context: LLMContext, exposed_entities: dict | None
    ) -> list[Tool]:
        """Return a list of LLM tools."""
        ignore_intents = self.IGNORE_INTENTS
        if not llm_context.device_id or not async_device_supports_timers(
            self.hass, llm_context.device_id
        ):
            ignore_intents = ignore_intents | {
                intent.INTENT_START_TIMER,
                intent.INTENT_CANCEL_TIMER,
                intent.INTENT_INCREASE_TIMER,
                intent.INTENT_DECREASE_TIMER,
                intent.INTENT_PAUSE_TIMER,
                intent.INTENT_UNPAUSE_TIMER,
                intent.INTENT_TIMER_STATUS,
            }

        intent_handlers = [
            intent_handler
            for intent_handler in intent.async_get(self.hass)
            if intent_handler.intent_type not in ignore_intents
        ]

        exposed_domains: set[str] | None = None
        if exposed_entities is not None:
            exposed_domains = {
                info["domain"] for info in exposed_entities["entities"].values()
            }

            intent_handlers = [
                intent_handler
                for intent_handler in intent_handlers
                if intent_handler.platforms is None
                or intent_handler.platforms & exposed_domains
            ]

        tools: list[Tool] = [
            IntentTool(self.cached_slugify(intent_handler.intent_type), intent_handler)
            for intent_handler in intent_handlers
        ]

        tools.append(GetDateTimeTool())

        if exposed_entities:
            if exposed_entities[CALENDAR_DOMAIN]:
                names = []
                for info in exposed_entities[CALENDAR_DOMAIN].values():
                    names.extend(info["names"].split(", "))
                tools.append(CalendarGetEventsTool(names))

            if exposed_domains is not None and TODO_DOMAIN in exposed_domains:
                names = []
                for info in exposed_entities["entities"].values():
                    if info["domain"] != TODO_DOMAIN:
                        continue
                    names.extend(info["names"].split(", "))
                tools.append(TodoGetItemsTool(names))

            tools.extend(
                ScriptTool(self.hass, script_entity_id)
                for script_entity_id in exposed_entities[SCRIPT_DOMAIN]
            )

        if exposed_domains:
            tools.append(GetLiveContextTool())

        return tools