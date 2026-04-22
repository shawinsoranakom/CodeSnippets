def __getitem__(self, k: str) -> Any:
        """Return the value of the widget with the given key.
        If the widget's value is currently stored in serialized form, it
        will be deserialized first.
        """
        wstate = self.states.get(k)
        if wstate is None:
            raise KeyError(k)

        if isinstance(wstate, Value):
            # The widget's value is already deserialized - return it directly.
            return wstate.value

        # The widget's value is serialized. We deserialize it, and return
        # the deserialized value.

        metadata = self.widget_metadata.get(k)
        if metadata is None:
            # No deserializer, which should only happen if state is
            # gotten from a reconnecting browser and the script is
            # trying to access it. Pretend it doesn't exist.
            raise KeyError(k)
        value_field_name = cast(
            ValueFieldName,
            wstate.value.WhichOneof("value"),
        )
        value = wstate.value.__getattribute__(value_field_name)

        if is_array_value_field_name(value_field_name):
            # Array types are messages with data in a `data` field
            value = value.data
        elif value_field_name == "json_value":
            value = json.loads(value)

        deserialized = metadata.deserializer(value, metadata.id)

        # Update metadata to reflect information from WidgetState proto
        self.set_widget_metadata(
            replace(
                metadata,
                value_type=value_field_name,
            )
        )

        self.states[k] = Value(deserialized)
        return deserialized