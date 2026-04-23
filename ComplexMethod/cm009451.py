def _generate_helper(
        self,
        prompts: list[str],
        stop: list[str] | None,
        run_managers: list[CallbackManagerForLLMRun],
        *,
        new_arg_supported: bool,
        **kwargs: Any,
    ) -> LLMResult:
        try:
            output = (
                self._generate(
                    prompts,
                    stop=stop,
                    # TODO: support multiple run managers
                    run_manager=run_managers[0] if run_managers else None,
                    **kwargs,
                )
                if new_arg_supported
                else self._generate(prompts, stop=stop)
            )
        except BaseException as e:
            for run_manager in run_managers:
                run_manager.on_llm_error(e, response=LLMResult(generations=[]))
            raise
        flattened_outputs = output.flatten()
        for manager, flattened_output in zip(
            run_managers, flattened_outputs, strict=False
        ):
            manager.on_llm_end(flattened_output)
        if run_managers:
            output.run = [
                RunInfo(run_id=run_manager.run_id) for run_manager in run_managers
            ]
        return output