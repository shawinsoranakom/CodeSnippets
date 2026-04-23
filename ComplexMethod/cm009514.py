def stream(
        self,
        input: Input,
        config: RunnableConfig | None = None,
        **kwargs: Any | None,
    ) -> Iterator[Output]:
        """First evaluates the condition, then delegate to `True` or `False` branch.

        Args:
            input: The input to the `Runnable`.
            config: The configuration for the `Runnable`.
            **kwargs: Additional keyword arguments to pass to the `Runnable`.

        Yields:
            The output of the branch that was run.
        """
        config = ensure_config(config)
        callback_manager = get_callback_manager_for_config(config)
        run_manager = callback_manager.on_chain_start(
            None,
            input,
            name=config.get("run_name") or self.get_name(),
            run_id=config.pop("run_id", None),
        )
        final_output: Output | None = None
        final_output_supported = True

        try:
            for idx, branch in enumerate(self.branches):
                condition, runnable = branch

                expression_value = condition.invoke(
                    input,
                    config=patch_config(
                        config,
                        callbacks=run_manager.get_child(tag=f"condition:{idx + 1}"),
                    ),
                )

                if expression_value:
                    for chunk in runnable.stream(
                        input,
                        config=patch_config(
                            config,
                            callbacks=run_manager.get_child(tag=f"branch:{idx + 1}"),
                        ),
                        **kwargs,
                    ):
                        yield chunk
                        if final_output_supported:
                            if final_output is None:
                                final_output = chunk
                            else:
                                try:
                                    final_output = final_output + chunk  # type: ignore[operator]
                                except TypeError:
                                    final_output = None
                                    final_output_supported = False
                    break
            else:
                for chunk in self.default.stream(
                    input,
                    config=patch_config(
                        config,
                        callbacks=run_manager.get_child(tag="branch:default"),
                    ),
                    **kwargs,
                ):
                    yield chunk
                    if final_output_supported:
                        if final_output is None:
                            final_output = chunk
                        else:
                            try:
                                final_output = final_output + chunk  # type: ignore[operator]
                            except TypeError:
                                final_output = None
                                final_output_supported = False
        except BaseException as e:
            run_manager.on_chain_error(e)
            raise
        run_manager.on_chain_end(final_output)