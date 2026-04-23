async def async_set_random_effect(
        self,
        brightness: int,
        duration: int,
        transition: int,
        segments: list[int],
        fadeoff: int,
        init_states: tuple[int, int, int],
        random_seed: int,
        backgrounds: Sequence[tuple[int, int, int]] | None = None,
        hue_range: tuple[int, int] | None = None,
        saturation_range: tuple[int, int] | None = None,
        brightness_range: tuple[int, int] | None = None,
        transition_range: tuple[int, int] | None = None,
    ) -> None:
        """Set a random effect."""
        effect: dict[str, Any] = {
            **_async_build_base_effect(brightness, duration, transition, segments),
            "type": "random",
            "init_states": [init_states],
            "random_seed": random_seed,
        }
        if backgrounds:
            effect["backgrounds"] = backgrounds
        if fadeoff:
            effect["fadeoff"] = fadeoff
        if hue_range:
            effect["hue_range"] = hue_range
        if saturation_range:
            effect["saturation_range"] = saturation_range
        if brightness_range:
            effect["brightness_range"] = brightness_range
            effect["brightness"] = min(
                brightness_range[1], max(brightness, brightness_range[0])
            )
        if transition_range:
            effect["transition_range"] = transition_range
            effect["transition"] = 0
        try:
            await self._effect_module.set_custom_effect(effect)
        except KasaException as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_custom_effect",
                translation_placeholders={
                    "effect": str(effect),
                    "exc": str(ex),
                },
            ) from ex