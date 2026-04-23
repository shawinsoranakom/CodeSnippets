def __init__(
        self,
        config_entry: WyomingConfigEntry,
        service: WyomingService,
    ) -> None:
        """Set up provider."""
        super().__init__()

        self.service = service

        self._intent_service: IntentProgram | None = None
        self._handle_service: HandleProgram | None = None

        for maybe_intent in self.service.info.intent:
            if maybe_intent.installed:
                self._intent_service = maybe_intent
                break

        for maybe_handle in self.service.info.handle:
            if maybe_handle.installed:
                self._handle_service = maybe_handle
                break

        model_languages: set[str] = set()

        if self._intent_service is not None:
            for intent_model in self._intent_service.models:
                if intent_model.installed:
                    model_languages.update(intent_model.languages)

            self._attr_name = self._intent_service.name
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )
        elif self._handle_service is not None:
            for handle_model in self._handle_service.models:
                if handle_model.installed:
                    model_languages.update(handle_model.languages)

            self._attr_name = self._handle_service.name

        self._supported_languages = list(model_languages)
        self._attr_unique_id = f"{config_entry.entry_id}-conversation"