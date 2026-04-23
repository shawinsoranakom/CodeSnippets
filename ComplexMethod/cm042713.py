def _process_spider_output(  # noqa: PLR0912
        self,
        response: Response,
        result: Iterable[_T] | AsyncIterator[_T],
        start_index: int = 0,
    ) -> Generator[Deferred[Any], Any, MutableChain[_T] | MutableAsyncChain[_T]]:
        # items in this iterable do not need to go through the process_spider_output
        # chain, they went through it already from the process_spider_exception method
        recovered: MutableChain[_T] | MutableAsyncChain[_T]
        last_result_is_async = isinstance(result, AsyncIterator)
        recovered = MutableAsyncChain() if last_result_is_async else MutableChain()

        # There are three cases for the middleware: def foo, async def foo, def foo + async def foo_async.
        # 1. def foo. Sync iterables are passed as is, async ones are downgraded.
        # 2. async def foo. Sync iterables are upgraded, async ones are passed as is.
        # 3. def foo + async def foo_async. Iterables are passed to the respective method.
        # Storing methods and method tuples in the same list is weird but we should be able to roll this back
        # when we drop this compatibility feature.

        method_list = islice(self.methods["process_spider_output"], start_index, None)
        for method_index, method_pair in enumerate(method_list, start=start_index):
            if method_pair is None:
                continue
            need_upgrade = need_downgrade = False
            if isinstance(method_pair, tuple):
                # This tuple handling is only needed until _async compatibility methods are removed.
                method_sync, method_async = method_pair
                method = method_async if last_result_is_async else method_sync
            else:
                method = method_pair
                if not last_result_is_async and isasyncgenfunction(method):
                    need_upgrade = True
                elif last_result_is_async and not isasyncgenfunction(method):
                    need_downgrade = True
            try:
                if need_upgrade:
                    # Iterable -> AsyncIterator
                    result = as_async_generator(result)
                elif need_downgrade:
                    logger.warning(
                        f"Async iterable passed to {global_object_name(method)} was"
                        f" downgraded to a non-async one. This is deprecated and will"
                        f" stop working in a future version of Scrapy. Please see"
                        f" https://docs.scrapy.org/en/latest/topics/coroutines.html#for-middleware-users"
                        f" for more information."
                    )
                    assert isinstance(result, AsyncIterator)
                    # AsyncIterator -> Iterable
                    result = yield deferred_from_coro(collect_asyncgen(result))
                    if isinstance(recovered, AsyncIterator):
                        recovered_collected = yield deferred_from_coro(
                            collect_asyncgen(recovered)
                        )
                        recovered = MutableChain(recovered_collected)
                # might fail directly if the output value is not a generator
                if method in self._mw_methods_requiring_spider:
                    result = method(
                        response=response, result=result, spider=self._spider
                    )
                else:
                    result = method(response=response, result=result)
            except Exception as ex:
                exception_result: Failure | MutableChain[_T] | MutableAsyncChain[_T] = (
                    self._process_spider_exception(response, ex, method_index + 1)
                )
                if isinstance(exception_result, Failure):
                    raise
                return exception_result
            if _isiterable(result):
                result = self._evaluate_iterable(
                    response, result, method_index + 1, recovered
                )
            else:
                if iscoroutine(result):
                    result.close()  # Silence warning about not awaiting
                    msg = (
                        f"{global_object_name(method)} must be an asynchronous "
                        f"generator (i.e. use yield)"
                    )
                else:
                    msg = (
                        f"{global_object_name(method)} must return an iterable, got "
                        f"{type(result)}"
                    )
                raise _InvalidOutput(msg)
            last_result_is_async = isinstance(result, AsyncIterator)

        if last_result_is_async:
            return MutableAsyncChain(result, recovered)
        return MutableChain(result, recovered)