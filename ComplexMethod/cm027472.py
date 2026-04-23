async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        # == Get key parameters ==
        if ATTR_EFFECT not in kwargs and ATTR_HS_COLOR in kwargs:
            effect = KEY_EFFECT_SOLID
        else:
            effect = kwargs.get(ATTR_EFFECT, self._effect)
        rgb_color: Sequence[int]
        if ATTR_HS_COLOR in kwargs:
            rgb_color = color_util.color_hs_to_RGB(*kwargs[ATTR_HS_COLOR])
        else:
            rgb_color = self._rgb_color

        # == Set brightness ==
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            for item in self._client.adjustment or []:
                if (
                    const.KEY_ID in item
                    and not await self._client.async_send_set_adjustment(
                        **{
                            const.KEY_ADJUSTMENT: {
                                const.KEY_BRIGHTNESS: int(
                                    round((float(brightness) * 100) / 255)
                                ),
                                const.KEY_ID: item[const.KEY_ID],
                            }
                        }
                    )
                ):
                    return

        # == Set an effect
        if effect and effect != KEY_EFFECT_SOLID:
            if not await self._client.async_send_set_effect(
                **{
                    const.KEY_PRIORITY: self._get_option(CONF_PRIORITY),
                    const.KEY_EFFECT: {const.KEY_NAME: effect},
                    const.KEY_ORIGIN: DEFAULT_ORIGIN,
                }
            ):
                return

        # == Set a color
        elif not await self._client.async_send_set_color(
            **{
                const.KEY_PRIORITY: self._get_option(CONF_PRIORITY),
                const.KEY_COLOR: rgb_color,
                const.KEY_ORIGIN: DEFAULT_ORIGIN,
            }
        ):
            return