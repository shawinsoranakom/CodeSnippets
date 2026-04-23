def process_turn_on_params(
    siren: SirenEntity, params: SirenTurnOnServiceParameters
) -> SirenTurnOnServiceParameters:
    """Process turn_on service params.

    Filters out unsupported params and validates the rest.
    """

    if not siren.supported_features & SirenEntityFeature.TONES:
        params.pop(ATTR_TONE, None)
    elif (tone := params.get(ATTR_TONE)) is not None:
        # Raise an exception if the specified tone isn't available
        is_tone_dict_value = bool(
            isinstance(siren.available_tones, dict)
            and tone in siren.available_tones.values()
        )
        if not siren.available_tones or (
            tone not in siren.available_tones and not is_tone_dict_value
        ):
            raise ValueError(
                f"Invalid tone specified for entity {siren.entity_id}: {tone}, "
                "check the available_tones attribute for valid tones to pass in"
            )

        # If available tones is a dict, and the tone provided is a dict value, we need
        # to transform it to the corresponding dict key before returning
        if is_tone_dict_value:
            assert isinstance(siren.available_tones, dict)
            params[ATTR_TONE] = next(
                key for key, value in siren.available_tones.items() if value == tone
            )

    if not siren.supported_features & SirenEntityFeature.DURATION:
        params.pop(ATTR_DURATION, None)
    if not siren.supported_features & SirenEntityFeature.VOLUME_SET:
        params.pop(ATTR_VOLUME_LEVEL, None)

    return params