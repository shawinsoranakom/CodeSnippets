def _integrate_langchain_traces(self) -> None:
        """Merge LangChain handler traces into the appropriate component step.

        Also converts LangChain objects in the steps to JSON-serializable format,
        since _convert_step_objects_recursively is skipped when _has_external_trace=True.
        """
        if not self.langchain_handler or not hasattr(self.langchain_handler, "_traces_by_root"):
            return

        langchain_traces = self.langchain_handler._traces_by_root
        if not langchain_traces:
            return

        # Find target component: prefer Agent, then fall back to LLM/chain types
        target_component = None
        for component_step in self.component_steps.values():
            if component_step.name in AGENT_NAMES:
                target_component = component_step
                break

        if target_component is None:
            for component_step in self.component_steps.values():
                if (
                    hasattr(component_step, "step_type")
                    and hasattr(component_step.step_type, "value")
                    and component_step.step_type.value
                    in [
                        "llm",
                        "chain",
                        "agent",
                        "chat_completion",
                    ]
                ):
                    target_component = component_step
                    break

        for lc_trace in langchain_traces.values():
            for lc_step in lc_trace.steps:
                # Convert LangChain objects before integration.
                # In the external trace path, the SDK skips _convert_step_objects_recursively,
                # so raw LangChain objects (BaseMessage, etc.) remain in inputs/output.
                # We must convert them here to ensure JSON serialization works in to_dict().
                self._convert_langchain_step(lc_step)
                if target_component:
                    target_component.add_nested_step(lc_step)

        # Clear handler's traces after integration
        self.langchain_handler._traces_by_root.clear()