async def call_spider_async(
        self, result: Response | Failure, request: Request
    ) -> Iterable[Any] | AsyncIterator[Any]:
        """Call the request callback or errback with the response or failure.

        .. versionadded:: 2.13
        """
        await _defer_sleep_async()
        assert self.crawler.spider
        if isinstance(result, Response):
            if getattr(result, "request", None) is None:
                result.request = request
            assert result.request
            callback = result.request.callback or self.crawler.spider._parse
            warn_on_generator_with_return_value(self.crawler.spider, callback)
            output = callback(result, **result.request.cb_kwargs)
            if isinstance(output, Deferred):
                warnings.warn(
                    f"{callback} returned a Deferred."
                    f" Returning Deferreds from spider callbacks is deprecated.",
                    ScrapyDeprecationWarning,
                    stacklevel=2,
                )
        else:  # result is a Failure
            # TODO: properly type adding this attribute to a Failure
            result.request = request  # type: ignore[attr-defined]
            if not request.errback:
                result.raiseException()
            warn_on_generator_with_return_value(self.crawler.spider, request.errback)
            output = request.errback(result)
            if isinstance(output, Failure):
                output.raiseException()
            # else the errback returned actual output (like a callback),
            # which needs to be passed to iterate_spider_output()
            if isinstance(output, Deferred):
                warnings.warn(
                    f"{request.errback} returned a Deferred."
                    f" Returning Deferreds from spider errbacks is deprecated.",
                    ScrapyDeprecationWarning,
                    stacklevel=2,
                )
        return await ensure_awaitable(iterate_spider_output(output))