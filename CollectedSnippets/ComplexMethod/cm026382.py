async def _do_provision() -> None:
            # mypy is not aware that we can't get here without having these set already
            assert self._credentials is not None
            assert self._device is not None
            assert self._discovery_info is not None

            # Register future before provisioning starts so other integrations
            # can register their flow IDs as soon as they discover the device
            ble_mac = format_mac(self._discovery_info.address)

            errors = {}
            async with self._async_provision_context(ble_mac) as future:
                try:
                    redirect_url = await self._try_call(
                        self._device.provision(
                            self._credentials.ssid, self._credentials.password, None
                        )
                    )
                except AbortFlow as err:
                    self._provision_result = self.async_abort(reason=err.reason)
                    return
                except improv_ble_errors.ProvisioningFailed as err:
                    if err.error == Error.NOT_AUTHORIZED:
                        _LOGGER.debug("Need authorization when calling provision")
                        self._provision_result = await self.async_step_authorize()
                        return
                    if err.error == Error.UNABLE_TO_CONNECT:
                        self._credentials = None
                        errors["base"] = "unable_to_connect"
                        # Only for UNABLE_TO_CONNECT do we continue to show the form with an error
                    else:
                        self._provision_result = self.async_abort(reason="unknown")
                        return
                else:
                    _LOGGER.debug(
                        "Provision successful, redirect URL: %s", redirect_url
                    )
                    # Clear match history so device can be rediscovered if factory reset.
                    # This ensures that if the device is factory reset in the future,
                    # it will trigger a new discovery flow.
                    bluetooth.async_clear_address_from_match_history(
                        self.hass, self._discovery_info.address
                    )
                    # Abort all flows in progress with same unique ID
                    for flow in self._async_in_progress(include_uninitialized=True):
                        flow_unique_id = flow["context"].get("unique_id")
                        if (
                            flow["flow_id"] != self.flow_id
                            and self.unique_id == flow_unique_id
                        ):
                            self.hass.config_entries.flow.async_abort(flow["flow_id"])

                    # Wait for another integration to discover and register flow chaining
                    next_flow_id: str | None = None

                    try:
                        next_flow_id = await asyncio.wait_for(
                            future, timeout=PROVISIONING_TIMEOUT
                        )
                    except TimeoutError:
                        _LOGGER.debug(
                            "Timeout waiting for next flow, proceeding with URL redirect"
                        )

                    if next_flow_id:
                        _LOGGER.debug("Received next flow ID: %s", next_flow_id)
                        self._provision_result = self.async_abort(
                            reason="provision_successful",
                            next_flow=(FlowType.CONFIG_FLOW, next_flow_id),
                        )
                        return

                    if redirect_url:
                        self._provision_result = self.async_abort(
                            reason="provision_successful_url",
                            description_placeholders={"url": redirect_url},
                        )
                        return
                    self._provision_result = self.async_abort(
                        reason="provision_successful"
                    )
                    return

            # If we reach here, we had UNABLE_TO_CONNECT error
            self._provision_result = self.async_show_form(
                step_id="provision", data_schema=STEP_PROVISION_SCHEMA, errors=errors
            )
            return