def finalize_registered_values(self) -> None:
        task_ctx = TaskContext.current()

        if not (register_projections := task_ctx.get_register_projections()):
            return

        registered_values = {}
        registered_errors = []

        for var_name, expression in register_projections.items():
            try:
                registered_values[var_name] = task_ctx.task_templar.template(expression)
            except Exception as ex:
                event = _error_factory.ControllerEventFactory.from_exception(ex, False)
                event_message = _event_utils.format_event_brief_message(event)
                undef_message = f"The variable {var_name!r} is undefined because its register expression failed: {event_message}"
                undef_value = trust_as_template(f"{{{{ undef({undef_message!r}) }}}}")

                if expression_origin := _tags.Origin.get_tag(expression.expression):
                    undef_value = expression_origin.tag(undef_value)

                registered_values[var_name] = undef_value

                try:
                    raise Exception(f"Register projection {var_name!r} failed.") from ex
                except Exception as ex:
                    registered_errors.append(ex)

        # RPFIX-9: FUTURE: merge registered_values into the pending VariableLayer.REGISTER_VARS layer instead of having a separate field
        self.registered_values = registered_values

        if not registered_errors:
            return

        chain = (
            _messages.EventChain(
                msg_reason="The original task error before register failed was:",
                traceback_reason="The above exception occurred before the following exception:",
                event=self.exception.event,
            )
            if self.exception
            else None
        )

        try:
            raise ExceptionGroup(
                f"Task failed due to errors in {len(registered_errors)} out of {len(register_projections)} register projections.",
                registered_errors,
            )
        except ExceptionGroup as ex:
            event = _error_factory.ControllerEventFactory.from_exception(ex, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR))
            event = dataclasses.replace(event, chain=chain)

            self.failed = True
            self.exception = _messages.ErrorSummary(
                event=event,
            )