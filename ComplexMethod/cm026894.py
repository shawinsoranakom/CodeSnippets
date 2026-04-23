async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        _LOGGER.debug("async_send_command %s with %s", command, params)
        if params is None:
            params = {}
        elif isinstance(params, list):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="vacuum_send_command_params_dict",
            )

        if command in ["spot_area", "custom_area"]:
            if params is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="vacuum_send_command_params_required",
                    translation_placeholders={"command": command},
                )
            if self._capability.clean.action.area is None:
                info = self._device.device_info
                name = info.get("nick", info["name"])
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="vacuum_send_command_area_not_supported",
                    translation_placeholders={"name": name},
                )

            if command == "spot_area":
                await self._device.execute_command(
                    self._capability.clean.action.area(
                        CleanMode.SPOT_AREA,
                        params["rooms"],
                        params.get("cleanings", 1),
                    )
                )
            elif command == "custom_area":
                await self._device.execute_command(
                    self._capability.clean.action.area(
                        CleanMode.CUSTOM_AREA,
                        params["coordinates"],
                        params.get("cleanings", 1),
                    )
                )
        else:
            await self._device.execute_command(
                self._capability.custom.set(command, params)
            )