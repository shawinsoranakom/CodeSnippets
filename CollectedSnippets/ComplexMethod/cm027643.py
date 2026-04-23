async def _async_step_call_service(self) -> None:
        """Call the service specified in the action."""
        self._step_log("call service")

        params = service.async_prepare_call_from_config(
            self._hass, self._action, self._variables
        )

        # Validate response data parameters. This check ignores services that do
        # not exist which will raise an appropriate error in the service call below.
        response_variable = self._action.get(CONF_RESPONSE_VARIABLE)
        return_response = response_variable is not None
        if self._hass.services.has_service(params[CONF_DOMAIN], params[CONF_SERVICE]):
            supports_response = self._hass.services.supports_response(
                params[CONF_DOMAIN], params[CONF_SERVICE]
            )
            if supports_response == SupportsResponse.ONLY and not return_response:
                raise vol.Invalid(
                    f"Script requires '{CONF_RESPONSE_VARIABLE}' for response data "
                    f"for service call {params[CONF_DOMAIN]}.{params[CONF_SERVICE]}"
                )
            if supports_response == SupportsResponse.NONE and return_response:
                raise vol.Invalid(
                    f"Script does not support '{CONF_RESPONSE_VARIABLE}' for service "
                    f"'{params[CONF_DOMAIN]}.{params[CONF_SERVICE]}' which does not support response data."
                )

        running_script = (
            params[CONF_DOMAIN] == "automation" and params[CONF_SERVICE] == "trigger"
        ) or params[CONF_DOMAIN] in ("python_script", "script")
        trace_set_result(params=params, running_script=running_script)
        response_data = await self._async_run_long_action(
            self._hass.async_create_task_internal(
                self._hass.services.async_call(
                    **params,
                    blocking=True,
                    context=self._context,
                    return_response=return_response,
                ),
                eager_start=True,
            )
        )
        if response_variable:
            self._variables[response_variable] = response_data