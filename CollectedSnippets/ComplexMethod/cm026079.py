async def async_pair_next_protocol(self) -> ConfigFlowResult:
        """Start pairing process for the next available protocol."""
        await self._async_cleanup()

        # Any more protocols to pair? Else bail out here
        if not self.protocols_to_pair:
            return await self._async_get_entry()

        self.protocol = self.protocols_to_pair.popleft()
        assert self.atv
        service = self.atv.get_service(self.protocol)

        if service is None:
            _LOGGER.debug(
                "%s does not support pairing (cannot find a corresponding service)",
                self.protocol,
            )
            return await self.async_pair_next_protocol()

        # Service requires a password
        if service.requires_password:
            return await self.async_step_password()

        # Figure out, depending on protocol, what kind of pairing is needed
        if service.pairing == PairingRequirement.Unsupported:
            _LOGGER.debug("%s does not support pairing", self.protocol)
            return await self.async_pair_next_protocol()
        if service.pairing == PairingRequirement.Disabled:
            return await self.async_step_protocol_disabled()
        if service.pairing == PairingRequirement.NotNeeded:
            _LOGGER.debug("%s does not require pairing", self.protocol)
            self.credentials[self.protocol.value] = None
            return await self.async_pair_next_protocol()

        _LOGGER.debug("%s requires pairing", self.protocol)

        # Protocol specific arguments
        pair_args: dict[str, Any] = {}
        if self.protocol in {Protocol.AirPlay, Protocol.Companion, Protocol.DMAP}:
            pair_args["name"] = "Home Assistant"
        if self.protocol == Protocol.DMAP:
            pair_args["zeroconf"] = await zeroconf.async_get_instance(self.hass)

        # Initiate the pairing process
        abort_reason = None
        session = async_get_clientsession(self.hass)
        self.pairing = await pair(
            self.atv, self.protocol, self.hass.loop, session=session, **pair_args
        )
        try:
            await self.pairing.begin()
        except exceptions.ConnectionFailedError:
            return await self.async_step_service_problem()
        except exceptions.BackOffError:
            abort_reason = "backoff"
        except exceptions.PairingError:
            _LOGGER.exception("Authentication problem")
            abort_reason = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            abort_reason = "unknown"

        if abort_reason:
            await self._async_cleanup()
            return self.async_abort(reason=abort_reason)

        # Choose step depending on if PIN is required from user or not
        if self.pairing.device_provides_pin:
            return await self.async_step_pair_with_pin()

        return await self.async_step_pair_no_pin()