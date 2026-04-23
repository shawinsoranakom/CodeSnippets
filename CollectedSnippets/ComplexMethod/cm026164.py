async def _async_update_data(self) -> dict[int, tuple[int, str]]:
        """Update all stored entities for Wolf SmartSet."""
        try:
            if not await self._wolf_client.fetch_system_state_list(
                self.device_id, self._gateway_id
            ):
                self._refetch_parameters = True
                raise UpdateFailed(
                    "Could not fetch values from server because device is offline."
                )
            if self._refetch_parameters:
                self.parameters = await fetch_parameters(
                    self._wolf_client, self._gateway_id, self.device_id
                )
                self._refetch_parameters = False
            values = {
                v.value_id: v.value
                for v in await self._wolf_client.fetch_value(
                    self._gateway_id, self.device_id, self.parameters
                )
            }
            return {
                parameter.parameter_id: (
                    parameter.value_id,
                    values[parameter.value_id],
                )
                for parameter in self.parameters
                if parameter.value_id in values
            }
        except RequestError as exception:
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception
        except FetchFailed as exception:
            raise UpdateFailed(
                f"Could not fetch values from server due to: {exception}"
            ) from exception
        except ParameterReadError as exception:
            self._refetch_parameters = True
            raise UpdateFailed(
                "Could not fetch values for parameter. Refreshing value IDs."
            ) from exception
        except InvalidAuth as exception:
            raise UpdateFailed("Invalid authentication during update.") from exception