async def parse_with_rules(
        self,
        response: Response,
        callback: CallbackT | None,
        cb_kwargs: dict[str, Any],
        follow: bool = True,
    ) -> AsyncIterator[Any]:
        if callback:
            cb_res = callback(response, **cb_kwargs) or ()
            if isinstance(cb_res, AsyncIterator):
                cb_res = await collect_asyncgen(cb_res)
            elif isinstance(cb_res, Awaitable):
                cb_res = await cb_res
            cb_res = self.process_results(response, cb_res)
            for request_or_item in iterate_spider_output(cb_res):
                yield request_or_item

        if follow and self._follow_links:
            for request_or_item in self._requests_to_follow(response):
                yield request_or_item