async def async_set_effect(self, effect) -> None:
        """Activate effect."""
        if not effect:
            return

        if effect == EFFECT_STOP:
            await self._bulb.async_stop_flow(light_type=self.light_type)
            return

        if effect in self.custom_effects_names:
            flow = Flow(**self.custom_effects[effect])
        elif effect in EFFECTS_MAP:
            flow = EFFECTS_MAP[effect]()
        elif effect == EFFECT_FAST_RANDOM_LOOP:
            flow = flows.random_loop(duration=250)
        elif effect == EFFECT_WHATSAPP:
            flow = flows.pulse(37, 211, 102, count=2)
        elif effect == EFFECT_FACEBOOK:
            flow = flows.pulse(59, 89, 152, count=2)
        elif effect == EFFECT_TWITTER:
            flow = flows.pulse(0, 172, 237, count=2)
        else:
            return

        await self._bulb.async_start_flow(flow, light_type=self.light_type)
        self._effect = effect