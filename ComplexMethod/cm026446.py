def _validate_state_class(options: dict[str, Any]) -> None:
    """Validate state class."""
    if (
        (state_class := options.get(CONF_STATE_CLASS))
        and (device_class := options.get(CONF_DEVICE_CLASS))
        and (state_classes := DEVICE_CLASS_STATE_CLASSES.get(device_class)) is not None
        and state_class not in state_classes
    ):
        sorted_state_classes = sorted(
            [f"'{state_class!s}'" for state_class in state_classes],
            key=str.casefold,
        )
        if len(sorted_state_classes) == 0:
            state_classes_string = "no state class"
        elif len(sorted_state_classes) == 1:
            state_classes_string = sorted_state_classes[0]
        else:
            state_classes_string = f"one of {', '.join(sorted_state_classes)}"

        raise vol.Invalid(
            f"'{state_class}' is not a valid state class for device class "
            f"'{device_class}'; expected {state_classes_string}"
        )