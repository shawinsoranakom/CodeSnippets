async def async_trigger(
        self,
        run_variables: dict[str, Any],
        context: Context | None = None,
        skip_condition: bool = False,
    ) -> ScriptRunResult | None:
        """Trigger automation.

        This method is a coroutine.
        """
        reason = ""
        alias = ""
        if "trigger" in run_variables:
            if "description" in run_variables["trigger"]:
                reason = f" by {run_variables['trigger']['description']}"
            if "alias" in run_variables["trigger"]:
                alias = f" trigger '{run_variables['trigger']['alias']}'"
        self._logger.debug("Automation%s triggered%s", alias, reason)

        # Create a new context referring to the old context.
        parent_id = None if context is None else context.id
        trigger_context = Context(parent_id=parent_id)

        with trace_automation(
            self.hass,
            self.unique_id,
            self.raw_config,
            self._blueprint_inputs,
            trigger_context,
            self._trace_config,
        ) as automation_trace:
            this = None
            if state := self.hass.states.get(self.entity_id):
                this = state.as_dict()
            variables: dict[str, Any] = {"this": this, **(run_variables or {})}
            if self._variables:
                try:
                    variables = self._variables.async_render(self.hass, variables)
                except TemplateError as err:
                    self._logger.error("Error rendering variables: %s", err)
                    automation_trace.set_error(err)
                    return None

            # Prepare tracing the automation
            automation_trace.set_trace(trace_get())

            # Set trigger reason
            trigger_description = variables.get("trigger", {}).get("description")
            automation_trace.set_trigger_description(trigger_description)

            # Add initial variables as the trigger step
            if "trigger" in variables and "idx" in variables["trigger"]:
                trigger_path = f"trigger/{variables['trigger']['idx']}"
            else:
                trigger_path = "trigger"
            trace_element = TraceElement(variables, trigger_path)
            trace_append_element(trace_element)

            if (
                not skip_condition
                and self._condition is not None
                and not self._condition(variables)
            ):
                self._logger.debug(
                    "Conditions not met, aborting automation. Condition summary: %s",
                    trace_get(clear=False),
                )
                script_execution_set("failed_conditions")
                return None

            self.async_set_context(trigger_context)
            event_data = {
                ATTR_NAME: self.name,
                ATTR_ENTITY_ID: self.entity_id,
            }
            if "trigger" in variables and "description" in variables["trigger"]:
                event_data[ATTR_SOURCE] = variables["trigger"]["description"]

            @callback
            def started_action() -> None:
                # This is always a callback from a coro so there is no
                # risk of this running in a thread which allows us to use
                # async_fire_internal
                self.hass.bus.async_fire_internal(
                    EVENT_AUTOMATION_TRIGGERED, event_data, context=trigger_context
                )

            # Make a new empty script stack; automations are allowed
            # to recursively trigger themselves
            script_stack_cv.set([])

            try:
                with trace_path("action"):
                    return await self.action_script.async_run(
                        variables, trigger_context, started_action
                    )
            except ServiceNotFound as err:
                async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"{self.entity_id}_service_not_found_{err.domain}.{err.service}",
                    is_fixable=True,
                    is_persistent=True,
                    severity=IssueSeverity.ERROR,
                    translation_key="service_not_found",
                    translation_placeholders={
                        "service": f"{err.domain}.{err.service}",
                        "entity_id": self.entity_id,
                        "name": self._attr_name or self.entity_id,
                        "edit": f"/config/automation/edit/{self.unique_id}",
                    },
                )
                automation_trace.set_error(err)
            except (vol.Invalid, HomeAssistantError) as err:
                self._logger.error(
                    "Error while executing automation %s: %s",
                    self.entity_id,
                    err,
                )
                automation_trace.set_error(err)
            except Exception as err:
                self._logger.exception("While executing automation %s", self.entity_id)
                automation_trace.set_error(err)

            return None