async def _async_step(self, log_exceptions: bool) -> None:
        continue_on_error = self._action.get(CONF_CONTINUE_ON_ERROR, False)

        with trace_path(str(self._step)):
            async with trace_action(
                self._hass, self, self._stop, self._variables.non_parallel_scope
            ) as trace_element:
                if self._stop.done():
                    return

                action = cv.determine_script_action(self._action)

                if CONF_ENABLED in self._action:
                    enabled = self._action[CONF_ENABLED]
                    if isinstance(enabled, Template):
                        try:
                            enabled = enabled.async_render(limited=True)
                        except exceptions.TemplateError as ex:
                            self._handle_exception(
                                ex,
                                continue_on_error,
                                self._log_exceptions or log_exceptions,
                            )
                    if not enabled:
                        self._log(
                            "Skipped disabled step %s",
                            self._action.get(CONF_ALIAS, action),
                        )
                        trace_set_result(enabled=False)
                        return

                handler = f"_async_step_{action}"
                try:
                    await getattr(self, handler)()
                except Exception as ex:  # noqa: BLE001
                    self._handle_exception(
                        ex, continue_on_error, self._log_exceptions or log_exceptions
                    )
                finally:
                    trace_element.update_variables(self._variables.non_parallel_scope)