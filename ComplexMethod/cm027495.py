async def async_step_pair(
        self, pair_info: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pair with a new HomeKit accessory."""
        # If async_step_pair is called with no pairing code then we do the M1
        # phase of pairing. If this is successful the device enters pairing
        # mode.

        # If it doesn't have a screen then the pin is static.

        # If it has a display it will display a pin on that display. In
        # this case the code is random. So we have to call the async_start_pairing
        # API before the user can enter a pin. But equally we don't want to
        # call async_start_pairing when the device is discovered, only when they
        # click on 'Configure' in the UI.

        # async_start_pairing will make the device show its pin and return a
        # callable. We call the callable with the pin that the user has typed
        # in.

        # Should never call this step without setting self.hkid
        assert self.hkid
        description_placeholders = {}

        errors = {}

        if self.controller is None:
            await self._async_setup_controller()

        assert self.controller

        if pair_info and self.finish_pairing:
            self.pairing = True
            code = pair_info["pairing_code"]
            try:
                code = ensure_pin_format(
                    code,
                    allow_insecure_setup_codes=pair_info.get(
                        "allow_insecure_setup_codes"
                    ),
                )
                pairing = await self.finish_pairing(code)
                return await self._entry_from_accessory(pairing)
            except aiohomekit.exceptions.MalformedPinError:
                # Library claimed pin was invalid before even making an API call
                errors["pairing_code"] = "authentication_error"
            except aiohomekit.AuthenticationError:
                # PairSetup M4 - SRP proof failed
                # PairSetup M6 - Ed25519 signature verification failed
                # PairVerify M4 - Decryption failed
                # PairVerify M4 - Device not recognised
                # PairVerify M4 - Ed25519 signature verification failed
                errors["pairing_code"] = "authentication_error"
                self.finish_pairing = None
            except aiohomekit.UnknownError:
                # An error occurred on the device whilst performing this
                # operation.
                errors["pairing_code"] = "unknown_error"
                self.finish_pairing = None
            except aiohomekit.MaxPeersError:
                # The device can't pair with any more accessories.
                errors["pairing_code"] = "max_peers_error"
                self.finish_pairing = None
            except aiohomekit.AccessoryNotFoundError:
                # Can no longer find the device on the network
                return self.async_abort(reason="accessory_not_found_error")
            except aiohomekit.AccessoryDisconnectedError as err:
                # The accessory has disconnected from the network
                return self.async_abort(
                    reason="accessory_disconnected_error",
                    description_placeholders={"error": str(err)},
                )
            except InsecureSetupCode:
                errors["pairing_code"] = "insecure_setup_code"
            except Exception as err:
                _LOGGER.exception("Pairing attempt failed with an unhandled exception")
                self.finish_pairing = None
                errors["pairing_code"] = "pairing_failed"
                description_placeholders["error"] = str(err)

        if not self.finish_pairing:
            # Its possible that the first try may have been busy so
            # we always check to see if self.finish_paring has been
            # set.
            try:
                discovery = await self.controller.async_find(self.hkid)
                self.finish_pairing = await discovery.async_start_pairing(self.hkid)

            except aiohomekit.BusyError:
                # Already performing a pair setup operation with a different
                # controller
                return await self.async_step_busy_error()
            except aiohomekit.MaxTriesError:
                # The accessory has received more than 100 unsuccessful auth
                # attempts.
                return await self.async_step_max_tries_error()
            except aiohomekit.UnavailableError:
                # The accessory is already paired - cannot try to pair again.
                return self.async_abort(reason="already_paired")
            except aiohomekit.AccessoryNotFoundError:
                # Can no longer find the device on the network
                return self.async_abort(reason="accessory_not_found_error")
            except aiohomekit.AccessoryDisconnectedError as err:
                # The accessory has disconnected from the network
                return self.async_abort(
                    reason="accessory_disconnected_error",
                    description_placeholders={"error": str(err)},
                )
            except IndexError:
                # TLV error, usually not in pairing mode
                _LOGGER.exception("Pairing communication failed")
                return await self.async_step_protocol_error()
            except Exception as err:
                _LOGGER.exception("Pairing attempt failed with an unhandled exception")
                errors["pairing_code"] = "pairing_failed"
                description_placeholders["error"] = str(err)

        return self._async_step_pair_show_form(errors, description_placeholders)