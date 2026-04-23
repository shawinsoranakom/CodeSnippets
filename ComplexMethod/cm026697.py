async def async_beolink_expand(
        self, beolink_jids: list[str] | None = None, all_discovered: bool = False
    ) -> None:
        """Expand a Beolink multi-room experience with a device or devices."""

        # Ensure that the current source is expandable
        if not self._beolink_sources[cast(str, self._source_change.id)]:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_source",
                translation_placeholders={
                    "invalid_source": cast(str, self._source_change.id),
                    "valid_sources": ", ".join(list(self._beolink_sources)),
                },
            )

        # Expand to all discovered devices
        if all_discovered:
            peers = await self._client.get_beolink_peers()

            for peer in peers:
                try:
                    await self._client.post_beolink_expand(jid=peer.jid)
                except NotFoundException:
                    _LOGGER.warning("Unable to expand to %s", peer.jid)

        # Try to expand to all defined devices
        elif beolink_jids:
            for beolink_jid in beolink_jids:
                try:
                    await self._client.post_beolink_expand(jid=beolink_jid)
                except NotFoundException:
                    _LOGGER.warning(
                        "Unable to expand to %s. Is the device available on the network?",
                        beolink_jid,
                    )