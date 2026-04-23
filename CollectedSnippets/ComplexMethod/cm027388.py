async def async_update(self):
        """Get the latest data from the remote SNMP capable host."""

        get_result = await get_cmd(*self._request_args)
        errindication, errstatus, errindex, restable = get_result

        if errindication and not self._accept_errors:
            _LOGGER.error("SNMP error: %s", errindication)
        elif errstatus and not self._accept_errors:
            _LOGGER.error(
                "SNMP error: %s at %s",
                errstatus.prettyPrint(),
                restable[-1][int(errindex) - 1] if errindex else "?",
            )
        elif (errindication or errstatus) and self._accept_errors:
            self.value = self._default_value
        else:
            for resrow in restable:
                self.value = self._decode_value(resrow[-1])