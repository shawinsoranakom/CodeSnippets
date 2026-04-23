async def aprep_prompts(
        self,
        input_list: list[dict[str, Any]],
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> tuple[list[PromptValue], list[str] | None]:
        """Prepare prompts from inputs."""
        stop = None
        if len(input_list) == 0:
            return [], stop
        if "stop" in input_list[0]:
            stop = input_list[0]["stop"]
        prompts = []
        for inputs in input_list:
            selected_inputs = {k: inputs[k] for k in self.prompt.input_variables}
            prompt = self.prompt.format_prompt(**selected_inputs)
            _colored_text = get_colored_text(prompt.to_string(), "green")
            _text = "Prompt after formatting:\n" + _colored_text
            if run_manager:
                await run_manager.on_text(_text, end="\n", verbose=self.verbose)
            if "stop" in inputs and inputs["stop"] != stop:
                msg = "If `stop` is present in any inputs, should be present in all."
                raise ValueError(msg)
            prompts.append(prompt)
        return prompts, stop