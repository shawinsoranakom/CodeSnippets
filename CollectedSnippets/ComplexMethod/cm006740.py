def _validate_and_run(self, *args, **kwargs) -> str:
        """Validate the tool call using SPARC and execute if valid."""
        # Check if validation should be bypassed
        if not self.sparc_component:
            return self._execute_tool(*args, **kwargs)

        # Prepare tool call for SPARC validation
        tool_call = {
            "id": str(uuid.uuid4()),
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self._prepare_arguments(*args, **kwargs)),
            },
        }

        if (
            isinstance(self.conversation_context, list)
            and self.conversation_context
            and isinstance(self.conversation_context[0], BaseMessage)
        ):
            logger.debug("Converting BaseMessages to list of dictionaries for conversation context of SPARC")
            self.conversation_context = [self._custom_message_to_dict(msg) for msg in self.conversation_context]

        logger.debug(
            f"Converted conversation context for SPARC for tool call:\n"
            f"{json.dumps(tool_call, indent=2)}\n{self.conversation_context=}"
        )

        try:
            # Run SPARC validation
            run_input = SPARCReflectionRunInput(
                messages=self.conversation_context + self.previous_tool_calls_in_current_step,
                tool_specs=self.tool_specs,
                tool_calls=[tool_call],
            )

            if self.current_conversation_context != self.conversation_context:
                logger.info("Updating conversation context for SPARC validation")
                self.current_conversation_context = self.conversation_context
                self.previous_tool_calls_in_current_step = []
            else:
                logger.info("Using existing conversation context for SPARC validation")
                self.previous_tool_calls_in_current_step.append(tool_call)

            # Check for missing tool specs and bypass if necessary
            if not self.tool_specs:
                logger.warning(f"No tool specs available for SPARC validation of {self.name}, executing directly")
                return self._execute_tool(*args, **kwargs)

            result = self.sparc_component.process(run_input, phase=AgentPhase.RUNTIME)
            logger.debug(f"SPARC validation result for tool {self.name}: {result.output.reflection_result}")

            # Check validation result
            if result.output.reflection_result.decision.name == "APPROVE":
                logger.info(f"✅ SPARC approved tool call for {self.name}")
                return self._execute_tool(*args, **kwargs)
            logger.info(f"❌ SPARC rejected tool call for {self.name}")
            return self._format_sparc_rejection(result.output.reflection_result)

        except (AttributeError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error during SPARC validation: {e}")
            # Execute directly on error
            return self._execute_tool(*args, **kwargs)