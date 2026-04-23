def batch(
        self,
        inputs: list[Input],
        config: RunnableConfig | list[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any | None,
    ) -> list[Output]:
        if not inputs:
            return []

        # setup callbacks and context
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
                input_,
                name=config.get("run_name") or self.get_name(),
                run_id=config.pop("run_id", None),
            )
            for cm, input_, config in zip(
                callback_managers, inputs, configs, strict=False
            )
        ]

        # invoke
        try:
            if return_exceptions:
                # Track which inputs (by index) failed so far
                # If an input has failed it will be present in this map,
                # and the value will be the exception that was raised.
                failed_inputs_map: dict[int, Exception] = {}
                for stepidx, step in enumerate(self.steps):
                    # Assemble the original indexes of the remaining inputs
                    # (i.e. the ones that haven't failed yet)
                    remaining_idxs = [
                        i for i in range(len(configs)) if i not in failed_inputs_map
                    ]
                    # Invoke the step on the remaining inputs
                    inputs = step.batch(
                        [
                            inp
                            for i, inp in zip(remaining_idxs, inputs, strict=False)
                            if i not in failed_inputs_map
                        ],
                        [
                            # each step a child run of the corresponding root run
                            patch_config(
                                config,
                                callbacks=rm.get_child(f"seq:step:{stepidx + 1}"),
                            )
                            for i, (rm, config) in enumerate(
                                zip(run_managers, configs, strict=False)
                            )
                            if i not in failed_inputs_map
                        ],
                        return_exceptions=return_exceptions,
                        **(kwargs if stepidx == 0 else {}),
                    )
                    # If an input failed, add it to the map
                    failed_inputs_map.update(
                        {
                            i: inp
                            for i, inp in zip(remaining_idxs, inputs, strict=False)
                            if isinstance(inp, Exception)
                        }
                    )
                    inputs = [inp for inp in inputs if not isinstance(inp, Exception)]
                    # If all inputs have failed, stop processing
                    if len(failed_inputs_map) == len(configs):
                        break

                # Reassemble the outputs, inserting Exceptions for failed inputs
                inputs_copy = inputs.copy()
                inputs = []
                for i in range(len(configs)):
                    if i in failed_inputs_map:
                        inputs.append(cast("Input", failed_inputs_map[i]))
                    else:
                        inputs.append(inputs_copy.pop(0))
            else:
                for i, step in enumerate(self.steps):
                    inputs = step.batch(
                        inputs,
                        [
                            # each step a child run of the corresponding root run
                            patch_config(
                                config, callbacks=rm.get_child(f"seq:step:{i + 1}")
                            )
                            for rm, config in zip(run_managers, configs, strict=False)
                        ],
                        return_exceptions=return_exceptions,
                        **(kwargs if i == 0 else {}),
                    )

        # finish the root runs
        except BaseException as e:
            for rm in run_managers:
                rm.on_chain_error(e)
            if return_exceptions:
                return cast("list[Output]", [e for _ in inputs])
            raise
        else:
            first_exception: Exception | None = None
            for run_manager, out in zip(run_managers, inputs, strict=False):
                if isinstance(out, Exception):
                    first_exception = first_exception or out
                    run_manager.on_chain_error(out)
                else:
                    run_manager.on_chain_end(out)
            if return_exceptions or first_exception is None:
                return cast("list[Output]", inputs)
            raise first_exception