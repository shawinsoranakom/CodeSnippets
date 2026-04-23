async def _async_update_data(self) -> None:
        """Update records."""
        _LOGGER.debug("Starting update for zone %s", self.zone["name"])
        try:
            records = await self.client.list_dns_records(
                zone_id=self.zone["id"], type="A"
            )
            _LOGGER.debug("Records: %s", records)

            target_records: list[str] = self.config_entry.data[CONF_RECORDS]

            location_info = await async_detect_location_info(
                async_get_clientsession(self.hass, family=socket.AF_INET)
            )

            if not location_info or not is_ipv4_address(location_info.ip):
                raise UpdateFailed("Could not get external IPv4 address")

            filtered_records = [
                record
                for record in records
                if record["name"] in target_records
                and record["content"] != location_info.ip
            ]

            if len(filtered_records) == 0:
                _LOGGER.debug("All target records are up to date")
                return

            await asyncio.gather(
                *[
                    self.client.update_dns_record(
                        zone_id=self.zone["id"],
                        record_id=record["id"],
                        record_content=location_info.ip,
                        record_name=record["name"],
                        record_type=record["type"],
                        record_proxied=record["proxied"],
                    )
                    for record in filtered_records
                ]
            )

            _LOGGER.debug("Update for zone %s is complete", self.zone["name"])

        except (
            pycfdns.AuthenticationException,
            pycfdns.ComunicationException,
        ) as e:
            raise UpdateFailed(
                f"Error updating zone {self.config_entry.data[CONF_ZONE]}"
            ) from e