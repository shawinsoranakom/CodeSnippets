async def async_update(self) -> None:
        """Update the state."""
        get_result = await get_cmd(*self._request_args)
        errindication, errstatus, errindex, restable = get_result

        if errindication:
            _LOGGER.error("SNMP error: %s", errindication)
        elif errstatus:
            _LOGGER.error(
                "SNMP error: %s at %s",
                errstatus.prettyPrint(),
                (errindex and restable[-1][int(errindex) - 1]) or "?",
            )
        else:
            for resrow in restable:
                if resrow[-1] == self._payload_on or resrow[-1] == Integer(
                    self._payload_on
                ):
                    self._state = True
                elif resrow[-1] == self._payload_off or resrow[-1] == Integer(
                    self._payload_off
                ):
                    self._state = False
                else:
                    _LOGGER.warning(
                        "Invalid payload '%s' received for entity %s, state is unknown",
                        resrow[-1],
                        self.entity_id,
                    )
                    self._state = None