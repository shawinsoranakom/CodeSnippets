async def _agenerate_helper(
        self,
        prompts: list[str],
        stop: list[str] | None,
        run_managers: list[AsyncCallbackManagerForLLMRun],
        *,
        new_arg_supported: bool,
        **kwargs: Any,
    ) -> LLMResult:
        try:
            output = (
                await self._agenerate(
                    prompts,
                    stop=stop,
                    run_manager=run_managers[0] if run_managers else None,
                    **kwargs,
                )
                if new_arg_supported
                else await self._agenerate(prompts, stop=stop)
            )
        except BaseException as e:
            await asyncio.gather(
                *[
                    run_manager.on_llm_error(e, response=LLMResult(generations=[]))
                    for run_manager in run_managers
                ]
            )
            raise
        flattened_outputs = output.flatten()
        await asyncio.gather(
            *[
                run_manager.on_llm_end(flattened_output)
                for run_manager, flattened_output in zip(
                    run_managers, flattened_outputs, strict=False
                )
            ]
        )
        if run_managers:
            output.run = [
                RunInfo(run_id=run_manager.run_id) for run_manager in run_managers
            ]
        return output