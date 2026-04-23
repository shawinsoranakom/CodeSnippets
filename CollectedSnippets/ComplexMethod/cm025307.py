async def async_update(api_category: str) -> dict:
        """Update the appropriate API data based on a category."""
        data: dict = {}

        try:
            if api_category == DATA_API_VERSIONS:
                data = await controller.api.versions()
            elif api_category == DATA_MACHINE_FIRMWARE_UPDATE_STATUS:
                data = await controller.machine.get_firmware_update_status()
            elif api_category == DATA_PROGRAMS:
                data = await controller.programs.all(include_inactive=True)
            elif api_category == DATA_PROVISION_SETTINGS:
                data = await controller.provisioning.settings()
            elif api_category == DATA_RESTRICTIONS_CURRENT:
                data = await controller.restrictions.current()
            elif api_category == DATA_RESTRICTIONS_UNIVERSAL:
                data = await controller.restrictions.universal()
            else:
                data = await controller.zones.all(details=True, include_inactive=True)
        except UnknownAPICallError:
            LOGGER.warning(
                "Skipping unsupported API call for controller %s: %s",
                controller.name,
                api_category,
            )
        except RainMachineError as err:
            raise UpdateFailed(err) from err

        return data