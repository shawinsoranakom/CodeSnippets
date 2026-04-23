def _download(
        self, request: Request
    ) -> Generator[Deferred[Any], Any, Response | Request]:
        assert self._slot is not None  # typing
        assert self.spider is not None

        self._slot.add_request(request)
        try:
            result: Response | Request
            if self._downloader_fetch_needs_spider:
                result = yield self.downloader.fetch(request, self.spider)
            else:
                result = yield self.downloader.fetch(request)
            if not isinstance(result, (Response, Request)):
                raise TypeError(
                    f"Incorrect type: expected Response or Request, got {type(result)}: {result!r}"
                )
            if isinstance(result, Response):
                if result.request is None:
                    result.request = request
                logkws = self.logformatter.crawled(result.request, result, self.spider)
                if logkws is not None:
                    logger.log(
                        *logformatter_adapter(logkws), extra={"spider": self.spider}
                    )
                self.signals.send_catch_log(
                    signal=signals.response_received,
                    response=result,
                    request=result.request,
                    spider=self.spider,
                )
            return result
        finally:
            self._slot.nextcall.schedule()