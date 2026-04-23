async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch the light on, change brightness, change color."""
        try:
            await self.coordinator.client.set_setting(
                self.appliance.info.ha_id,
                setting_key=SettingKey(self.bsh_key),
                value=True,
            )
        except HomeConnectError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="turn_on_light",
                translation_placeholders={
                    **get_dict_from_home_connect_error(err),
                    "entity_id": self.entity_id,
                },
            ) from err
        if self._color_key and self._custom_color_key:
            if (
                ATTR_RGB_COLOR in kwargs or ATTR_HS_COLOR in kwargs
            ) and self._enable_custom_color_value_key:
                try:
                    await self.coordinator.client.set_setting(
                        self.appliance.info.ha_id,
                        setting_key=self._color_key,
                        value=self._enable_custom_color_value_key,
                    )
                except HomeConnectError as err:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="select_light_custom_color",
                        translation_placeholders={
                            **get_dict_from_home_connect_error(err),
                            "entity_id": self.entity_id,
                        },
                    ) from err

            if ATTR_RGB_COLOR in kwargs:
                hex_val = color_util.color_rgb_to_hex(*kwargs[ATTR_RGB_COLOR])
                try:
                    await self.coordinator.client.set_setting(
                        self.appliance.info.ha_id,
                        setting_key=self._custom_color_key,
                        value=f"#{hex_val}",
                    )
                except HomeConnectError as err:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="set_light_color",
                        translation_placeholders={
                            **get_dict_from_home_connect_error(err),
                            "entity_id": self.entity_id,
                        },
                    ) from err
                return
            if (self._attr_brightness is not None or ATTR_BRIGHTNESS in kwargs) and (
                self._attr_hs_color is not None or ATTR_HS_COLOR in kwargs
            ):
                brightness = round(
                    color_util.brightness_to_value(
                        self._brightness_scale,
                        cast(int, kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness)),
                    )
                )

                hs_color = cast(
                    tuple[float, float], kwargs.get(ATTR_HS_COLOR, self._attr_hs_color)
                )

                rgb = color_util.color_hsv_to_RGB(hs_color[0], hs_color[1], brightness)
                hex_val = color_util.color_rgb_to_hex(*rgb)
                try:
                    await self.coordinator.client.set_setting(
                        self.appliance.info.ha_id,
                        setting_key=self._custom_color_key,
                        value=f"#{hex_val}",
                    )
                except HomeConnectError as err:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="set_light_color",
                        translation_placeholders={
                            **get_dict_from_home_connect_error(err),
                            "entity_id": self.entity_id,
                        },
                    ) from err
                return

        if self._brightness_key and ATTR_BRIGHTNESS in kwargs:
            brightness = round(
                color_util.brightness_to_value(
                    self._brightness_scale, kwargs[ATTR_BRIGHTNESS]
                )
            )
            try:
                await self.coordinator.client.set_setting(
                    self.appliance.info.ha_id,
                    setting_key=self._brightness_key,
                    value=brightness,
                )
            except HomeConnectError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="set_light_brightness",
                    translation_placeholders={
                        **get_dict_from_home_connect_error(err),
                        "entity_id": self.entity_id,
                    },
                ) from err