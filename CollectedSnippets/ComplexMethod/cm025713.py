def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the entity."""
        super().__init__(*args, **kwargs)
        # fill the event types based on the features the switch supports
        event_types: list[str] = []
        feature_map = int(
            self.get_matter_attribute_value(clusters.Switch.Attributes.FeatureMap)
        )
        if feature_map & SwitchFeature.kLatchingSwitch:
            # a latching switch only supports switch_latched event
            event_types.append("switch_latched")
        elif feature_map & SwitchFeature.kMomentarySwitchMultiPress:
            # Momentary switch with multi press support
            # NOTE: We ignore 'multi press ongoing' as it doesn't make a lot
            # of sense and many devices do not support it.
            # Instead we report on the 'multi press complete' event with the number
            # of presses.
            max_presses_supported = self.get_matter_attribute_value(
                clusters.Switch.Attributes.MultiPressMax
            )
            max_presses_supported = min(max_presses_supported or 2, 8)
            for i in range(max_presses_supported):
                event_types.append(f"multi_press_{i + 1}")  # noqa: PERF401
        elif feature_map & SwitchFeature.kMomentarySwitch:
            # momentary switch without multi press support
            event_types.append("initial_press")
            if feature_map & SwitchFeature.kMomentarySwitchRelease:
                # momentary switch without multi press support can optionally support release
                event_types.append("short_release")

        # a momentary switch can optionally support long press
        if feature_map & SwitchFeature.kMomentarySwitchLongPress:
            event_types.append("long_press")
            event_types.append("long_release")

        self._attr_event_types = event_types