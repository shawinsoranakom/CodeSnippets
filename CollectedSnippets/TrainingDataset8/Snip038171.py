def register_widget(
        self, metadata: WidgetMetadata[T], user_key: Optional[str]
    ) -> RegisterWidgetResult[T]:
        """Register a widget with the SessionState.

        Returns
        -------
        RegisterWidgetResult[T]
            Contains the widget's current value, and a bool that will be True
            if the frontend needs to be updated with the current value.
        """
        widget_id = metadata.id

        self._set_widget_metadata(metadata)
        if user_key is not None:
            # If the widget has a user_key, update its user_key:widget_id mapping
            self._set_key_widget_mapping(widget_id, user_key)

        if widget_id not in self and (user_key is None or user_key not in self):
            # This is the first time the widget is registered, so we save its
            # value in widget state.
            deserializer = metadata.deserializer
            initial_widget_value = deepcopy(deserializer(None, metadata.id))
            self._new_widget_state.set_from_value(widget_id, initial_widget_value)

        # Get the current value of the widget for use as its return value.
        # We return a copy, so that reference types can't be accidentally
        # mutated by user code.
        widget_value = cast(T, self[widget_id])
        widget_value = deepcopy(widget_value)

        # widget_value_changed indicates to the caller that the widget's
        # current value is different from what is in the frontend.
        widget_value_changed = user_key is not None and self.is_new_state_value(
            user_key
        )

        return RegisterWidgetResult(widget_value, widget_value_changed)