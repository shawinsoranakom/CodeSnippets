async def send_telemetry_data(self, payload: BaseModel, path: str | None = None) -> None:
        if self.do_not_track:
            await logger.adebug("Telemetry tracking is disabled.")
            return

        if payload.client_type is None:
            payload.client_type = self.client_type

        url = f"{self.base_url}"
        if path:
            url = f"{url}/{path}"

        try:
            payload_dict = payload.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)

            # Add common fields to all payloads except VersionPayload
            if not isinstance(payload, VersionPayload):
                payload_dict.update(self.common_telemetry_fields)
            # Add timestamp dynamically
            if "timestamp" not in payload_dict:
                payload_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

            response = await self.client.get(url, params=payload_dict)
            if response.status_code != httpx.codes.OK:
                await logger.aerror(f"Failed to send telemetry data: {response.status_code} {response.text}")
            else:
                await logger.adebug("Telemetry data sent successfully.")
        except httpx.HTTPStatusError as err:
            await logger.aerror(f"HTTP error occurred: {err}.")
        except httpx.RequestError as err:
            await logger.aerror(f"Request error occurred: {err}.")
        except Exception as err:  # noqa: BLE001
            await logger.aerror(f"Unexpected error occurred: {err}.")