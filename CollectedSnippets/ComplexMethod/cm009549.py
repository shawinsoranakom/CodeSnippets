def batch(
        self,
        inputs: list[Input],
        config: RunnableConfig | list[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any | None,
    ) -> list[Output]:
        if self.exception_key is not None and not all(
            isinstance(input_, dict) for input_ in inputs
        ):
            msg = (
                "If 'exception_key' is specified then inputs must be dictionaries."
                f"However found a type of {type(inputs[0])} for input"
            )
            raise ValueError(msg)

        if not inputs:
            return []

        # setup callbacks
        configs = get_config_list(config, len(inputs))
        callback_managers = [
            CallbackManager.configure(
                inheritable_callbacks=config.get("callbacks"),
                local_callbacks=None,
                verbose=False,
                inheritable_tags=config.get("tags"),
                local_tags=None,
                inheritable_metadata=config.get("metadata"),
                local_metadata=None,
            )
            for config in configs
        ]
        # start the root runs, one per input
        run_managers = [
            cm.on_chain_start(
                None,
                input_ if isinstance(input_, dict) else {"input": input_},
                name=config.get("run_name") or self.get_name(),
                run_id=config.pop("run_id", None),
            )
            for cm, input_, config in zip(
                callback_managers, inputs, configs, strict=False
            )
        ]

        to_return: dict[int, Any] = {}
        run_again = dict(enumerate(inputs))
        handled_exceptions: dict[int, BaseException] = {}
        first_to_raise = None
        for runnable in self.runnables:
            outputs = runnable.batch(
                [input_ for _, input_ in sorted(run_again.items())],
                [
                    # each step a child run of the corresponding root run
                    patch_config(configs[i], callbacks=run_managers[i].get_child())
                    for i in sorted(run_again)
                ],
                return_exceptions=True,
                **kwargs,
            )
            for (i, input_), output in zip(
                sorted(run_again.copy().items()), outputs, strict=False
            ):
                if isinstance(output, BaseException) and not isinstance(
                    output, self.exceptions_to_handle
                ):
                    if not return_exceptions:
                        first_to_raise = first_to_raise or output
                    else:
                        handled_exceptions[i] = output
                    run_again.pop(i)
                elif isinstance(output, self.exceptions_to_handle):
                    if self.exception_key:
                        input_[self.exception_key] = output  # type: ignore[index]
                    handled_exceptions[i] = output
                else:
                    run_managers[i].on_chain_end(output)
                    to_return[i] = output
                    run_again.pop(i)
                    handled_exceptions.pop(i, None)
            if first_to_raise:
                raise first_to_raise
            if not run_again:
                break

        sorted_handled_exceptions = sorted(handled_exceptions.items())
        for i, error in sorted_handled_exceptions:
            run_managers[i].on_chain_error(error)
        if not return_exceptions and sorted_handled_exceptions:
            raise sorted_handled_exceptions[0][1]
        to_return.update(handled_exceptions)
        return [output for _, output in sorted(to_return.items())]