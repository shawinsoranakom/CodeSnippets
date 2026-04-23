def failure(
        cls, deserializer: WidgetDeserializer[T_co]
    ) -> "RegisterWidgetResult[T_co]":
        """The canonical way to construct a RegisterWidgetResult in cases
        where the true widget value could not be determined.
        """
        return cls(value=deserializer(None, ""), value_changed=False)