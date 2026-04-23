def _update_effect_list(self, _: dict[str, Any] | None = None) -> None:
        """Update Hyperion effects."""
        if not self._client.effects:
            return
        effect_list: list[str] = []
        hide_effects = self._get_option(CONF_EFFECT_HIDE_LIST)

        for effect in self._client.effects or []:
            if const.KEY_NAME in effect:
                effect_name = effect[const.KEY_NAME]
                if effect_name not in hide_effects:
                    effect_list.append(effect_name)

        self._effect_list = [
            effect for effect in self._static_effect_list if effect not in hide_effects
        ] + effect_list
        self.async_write_ha_state()