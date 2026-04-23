def _calculate_effect_list(self):
        """Calculate an effect list based on current status."""
        effects: list[AmbilightEffect] = []
        effects.extend(
            AmbilightEffect(mode=EFFECT_AUTO, style=style, algorithm=setting)
            for style, data in self._tv.ambilight_styles.items()
            for setting in data.get("menuSettings", [])
        )

        effects.extend(
            AmbilightEffect(mode=EFFECT_EXPERT, style=style, algorithm=algorithm)
            for style, data in self._tv.ambilight_styles.items()
            for algorithm in data.get("algorithms", [])
        )

        effects.extend(
            AmbilightEffect(mode=EFFECT_MODE, style=style)
            for style in self._tv.ambilight_modes
        )

        filtered_effects = [
            str(effect)
            for effect in effects
            if effect.is_valid() and effect.is_on(self._tv.powerstate)
        ]

        return sorted(filtered_effects)