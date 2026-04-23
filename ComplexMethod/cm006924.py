async def _get_output_result(self, output):
        """Computes and returns the result for a given output, applying caching and output options.

        If the output is cached and a value is already defined, returns the cached value. Otherwise,
        invokes the associated output method asynchronously, applies output options, updates the cache,
        and returns the result. Raises a ValueError if the output method is not defined, or a TypeError
        if the method invocation fails.
        """
        if output.cache and output.value != UNDEFINED:
            return output.value

        if output.method is None:
            msg = f'Output "{output.name}" does not have a method defined.'
            raise ValueError(msg)

        method = getattr(self, output.method)
        try:
            result = await method() if inspect.iscoroutinefunction(method) else await asyncio.to_thread(method)
        except TypeError as e:
            msg = f'Error running method "{output.method}": {e}'
            raise TypeError(msg) from e

        if (
            self._vertex is not None
            and isinstance(result, Message)
            and result.flow_id is None
            and self._vertex.graph.flow_id is not None
        ):
            result.set_flow_id(self._vertex.graph.flow_id)
        result = output.apply_options(result)
        output.value = result

        return result