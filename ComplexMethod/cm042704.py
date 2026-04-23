async def _process_start_next(self) -> None:
        """Processes the next item or request from Spider.start().

        If a request, it is scheduled. If an item, it is sent to item
        pipelines.
        """
        assert self._start is not None
        try:
            item_or_request = await self._start.__anext__()
        except StopAsyncIteration:
            self._start = None
        except Exception as exception:
            self._start = None
            exception_traceback = format_exc()
            logger.error(
                f"Error while reading start items and requests: {exception}.\n{exception_traceback}",
                exc_info=True,
            )
        else:
            if not self.spider:
                return  # spider already closed
            if isinstance(item_or_request, Request):
                self.crawl(item_or_request)
            else:
                assert self._slot is not None
                _schedule_coro(
                    self.scraper.start_itemproc_async(item_or_request, response=None)
                )
                self._slot.nextcall.schedule()