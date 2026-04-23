async def _process_request(
        self, request: Request, info: SpiderInfo, item: Any
    ) -> FileInfo:
        fp = self._fingerprinter.fingerprint(request)

        eb = request.errback
        request.callback = NO_CALLBACK
        request.errback = None

        # Return cached result if request was already seen
        if fp in info.downloaded:
            await _defer_sleep_async()
            cached_result = info.downloaded[fp]
            if isinstance(cached_result, Failure):
                if eb:
                    return eb(cached_result)
                cached_result.raiseException()
            return cached_result

        # Otherwise, wait for result
        wad: Deferred[FileInfo] = Deferred()
        if eb:
            wad.addErrback(eb)
        info.waiting[fp].append(wad)

        # Check if request is downloading right now to avoid doing it twice
        if fp in info.downloading:
            return await maybe_deferred_to_future(wad)

        # Download request checking media_to_download hook output first
        info.downloading.add(fp)
        await _defer_sleep_async()
        result: FileInfo | Failure
        try:
            file_info: FileInfo | None = await ensure_awaitable(
                self.media_to_download(request, info, item=item)
            )
            if file_info:
                # got a result without downloading
                result = file_info
            else:
                # download the result
                result = await self._check_media_to_download(request, info, item=item)
        except Exception:
            result = Failure()
            logger.exception(result)
        self._cache_result_and_execute_waiters(result, fp, info)
        return await maybe_deferred_to_future(wad)