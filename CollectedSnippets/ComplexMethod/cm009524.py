async def _abatch(
        self,
        inputs: list[Input],
        run_manager: list["AsyncCallbackManagerForChainRun"],
        config: list[RunnableConfig],
        **kwargs: Any,
    ) -> list[Output | Exception]:
        results_map: dict[int, Output] = {}

        not_set: list[Output] = []
        result = not_set
        try:
            async for attempt in self._async_retrying():
                with attempt:
                    # Retry for inputs that have not yet succeeded
                    # Determine which original indices remain.
                    remaining_indices = [
                        i for i in range(len(inputs)) if i not in results_map
                    ]
                    if not remaining_indices:
                        break
                    pending_inputs = [inputs[i] for i in remaining_indices]
                    pending_configs = [config[i] for i in remaining_indices]
                    pending_run_managers = [run_manager[i] for i in remaining_indices]
                    result = await super().abatch(
                        pending_inputs,
                        self._patch_config_list(
                            pending_configs, pending_run_managers, attempt.retry_state
                        ),
                        return_exceptions=True,
                        **kwargs,
                    )
                    # Register the results of the inputs that have succeeded, mapping
                    # back to their original indices.
                    first_exception = None
                    for offset, r in enumerate(result):
                        if isinstance(r, Exception):
                            if not first_exception:
                                first_exception = r
                            continue
                        orig_idx = remaining_indices[offset]
                        results_map[orig_idx] = r
                    # If any exception occurred, raise it, to retry the failed ones
                    if first_exception:
                        raise first_exception
                if (
                    attempt.retry_state.outcome
                    and not attempt.retry_state.outcome.failed
                ):
                    attempt.retry_state.set_result(result)
        except RetryError as e:
            if result is not_set:
                result = cast("list[Output]", [e] * len(inputs))

        outputs: list[Output | Exception] = []
        for idx in range(len(inputs)):
            if idx in results_map:
                outputs.append(results_map[idx])
            else:
                outputs.append(result.pop(0))
        return outputs