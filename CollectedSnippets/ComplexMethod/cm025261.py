async def update_data(self) -> dict[str, ConsoleData]:
        """Fetch console data."""

        consoles: list[SmartglassConsole] = list(self.async_contexts())

        if not consoles and self.consoles is not None:
            consoles = list(self.consoles.values())
            self.consoles = None

        data: dict[str, ConsoleData] = {}
        for console in consoles:
            status = await self.client.smartglass.get_console_status(console.id)
            _LOGGER.debug("%s status: %s", console.name, status.model_dump())

            # Setup focus app
            app_details = (
                current_state.app_details
                if (current_state := self.data.get(console.id)) is not None
                and status.focus_app_aumid
                else None
            )

            if status.focus_app_aumid and (
                not current_state
                or status.focus_app_aumid != current_state.status.focus_app_aumid
            ):
                catalog_result = (
                    await self.client.catalog.get_product_from_alternate_id(
                        *self._resolve_app_id(status.focus_app_aumid)
                    )
                )

                if catalog_result.products:
                    app_details = catalog_result.products[0]

            data[console.id] = ConsoleData(status=status, app_details=app_details)

        return data