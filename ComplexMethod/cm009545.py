def _transform(
        self,
        chunks: Iterator[Input],
        run_manager: CallbackManagerForChainRun,
        config: RunnableConfig,
        **kwargs: Any,
    ) -> Iterator[Output]:
        final: Input
        got_first_val = False
        for ichunk in chunks:
            # By definitions, RunnableLambdas consume all input before emitting output.
            # If the input is not addable, then we'll assume that we can
            # only operate on the last chunk.
            # So we'll iterate until we get to the last chunk!
            if not got_first_val:
                final = ichunk
                got_first_val = True
            else:
                try:
                    final = final + ichunk  # type: ignore[operator]
                except TypeError:
                    final = ichunk

        if inspect.isgeneratorfunction(self.func):
            output: Output | None = None
            for chunk in call_func_with_variable_args(
                self.func, final, config, run_manager, **kwargs
            ):
                yield chunk
                if output is None:
                    output = chunk
                else:
                    try:
                        output = output + chunk
                    except TypeError:
                        output = chunk
        else:
            output = call_func_with_variable_args(
                self.func, final, config, run_manager, **kwargs
            )

        # If the output is a Runnable, use its stream output
        if isinstance(output, Runnable):
            recursion_limit = config["recursion_limit"]
            if recursion_limit <= 0:
                msg = (
                    f"Recursion limit reached when invoking {self} with input {final}."
                )
                raise RecursionError(msg)
            for chunk in output.stream(
                final,
                patch_config(
                    config,
                    callbacks=run_manager.get_child(),
                    recursion_limit=recursion_limit - 1,
                ),
            ):
                yield chunk
        elif not inspect.isgeneratorfunction(self.func):
            # Otherwise, just yield it
            yield cast("Output", output)