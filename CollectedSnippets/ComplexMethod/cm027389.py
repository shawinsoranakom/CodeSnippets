async def async_get_snmp_data(self):
        """Fetch MAC addresses from access point via SNMP."""
        devices = []
        if TYPE_CHECKING:
            assert self.request_args is not None

        engine, auth_data, target, context_data, object_type = self.request_args
        walker = bulk_walk_cmd(
            engine,
            auth_data,
            target,
            context_data,
            0,
            50,
            object_type,
            lexicographicMode=False,
        )
        async for errindication, errstatus, errindex, res in walker:
            if errindication:
                _LOGGER.error("SNMPLIB error: %s", errindication)
                return None
            if errstatus:
                _LOGGER.error(
                    "SNMP error: %s at %s",
                    errstatus.prettyPrint(),
                    (errindex and res[int(errindex) - 1][0]) or "?",
                )
                return None

            for _oid, value in res:
                if not is_end_of_mib(res):
                    try:
                        mac = binascii.hexlify(value.asOctets()).decode("utf-8")
                    except AttributeError:
                        continue
                    _LOGGER.debug("Found MAC address: %s", mac)
                    mac = ":".join([mac[i : i + 2] for i in range(0, len(mac), 2)])
                    devices.append({"mac": mac})
        return devices