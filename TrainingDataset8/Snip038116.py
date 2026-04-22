def register_widget(
        self, metadata: WidgetMetadata[T], user_key: Optional[str]
    ) -> RegisterWidgetResult[T]:
        with self._lock:
            if self._disconnected:
                return RegisterWidgetResult.failure(metadata.deserializer)

            return self._state.register_widget(metadata, user_key)