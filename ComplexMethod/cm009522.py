async def atransform(
        self,
        input: AsyncIterator[Other],
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[Other]:
        if self.afunc is None and self.func is None:
            async for chunk in self._atransform_stream_with_config(
                input, identity, config
            ):
                yield chunk
        else:
            got_first_chunk = False

            async for chunk in self._atransform_stream_with_config(
                input, identity, config
            ):
                yield chunk

                # By definitions, a function will operate on the aggregated
                # input. So we'll aggregate the input until we get to the last
                # chunk.
                # If the input is not addable, then we'll assume that we can
                # only operate on the last chunk.
                if not got_first_chunk:
                    final = chunk
                    got_first_chunk = True
                else:
                    try:
                        final = final + chunk  # type: ignore[operator]
                    except TypeError:
                        final = chunk

            if got_first_chunk:
                config = ensure_config(config)
                if self.afunc is not None:
                    await acall_func_with_variable_args(
                        self.afunc, final, config, **kwargs
                    )
                elif self.func is not None:
                    call_func_with_variable_args(self.func, final, config, **kwargs)