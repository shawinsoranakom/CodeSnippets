def _process_spider_exception(
        self,
        response: Response,
        exception: Exception,
        start_index: int = 0,
    ) -> MutableChain[_T] | MutableAsyncChain[_T]:
        # don't handle _InvalidOutput exception
        if isinstance(exception, _InvalidOutput):
            raise exception
        method_list = islice(
            self.methods["process_spider_exception"], start_index, None
        )
        for method_index, method in enumerate(method_list, start=start_index):
            if method is None:
                continue
            method = cast("Callable", method)
            if method in self._mw_methods_requiring_spider:
                result = method(
                    response=response, exception=exception, spider=self._spider
                )
            else:
                result = method(response=response, exception=exception)
            if _isiterable(result):
                # stop exception handling by handing control over to the
                # process_spider_output chain if an iterable has been returned
                dfd: Deferred[MutableChain[_T] | MutableAsyncChain[_T]] = (
                    self._process_spider_output(response, result, method_index + 1)
                )
                # _process_spider_output() returns a Deferred only because of downgrading so this can be
                # simplified when downgrading is removed.
                if dfd.called:
                    # the result is available immediately if _process_spider_output didn't do downgrading
                    return cast("MutableChain[_T] | MutableAsyncChain[_T]", dfd.result)
                # we forbid waiting here because otherwise we would need to return a deferred from
                # _process_spider_exception too, which complicates the architecture
                msg = f"Async iterable returned from {global_object_name(method)} cannot be downgraded"
                raise _InvalidOutput(msg)
            if result is None:
                continue
            msg = (
                f"{global_object_name(method)} must return None "
                f"or an iterable, got {type(result)}"
            )
            raise _InvalidOutput(msg)
        raise exception