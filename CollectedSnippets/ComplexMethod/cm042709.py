async def close_spider_async(self, *, reason: str = "cancelled") -> None:  # noqa: PLR0912
        """Close (cancel) spider and clear all its outstanding requests.

        .. versionadded:: 2.14
        """
        if self.spider is None:
            raise RuntimeError("Spider not opened")

        if self._slot is None:
            raise RuntimeError("Engine slot not assigned")

        if self._slot.closing is not None:
            await maybe_deferred_to_future(self._slot.closing)
            return

        spider = self.spider

        logger.info(
            "Closing spider (%(reason)s)", {"reason": reason}, extra={"spider": spider}
        )

        def log_failure(msg: str) -> None:
            logger.error(msg, exc_info=True, extra={"spider": spider})  # noqa: LOG014

        try:
            await self._slot.close()
        except Exception:
            log_failure("Slot close failure")

        try:
            self.downloader.close()
        except Exception:
            log_failure("Downloader close failure")

        try:
            await self.scraper.close_spider_async()
        except Exception:
            log_failure("Scraper close failure")

        if hasattr(self._slot.scheduler, "close"):
            try:
                if (d := self._slot.scheduler.close(reason)) is not None:
                    await maybe_deferred_to_future(d)
            except Exception:
                log_failure("Scheduler close failure")

        try:
            await self.signals.send_catch_log_async(
                signal=signals.spider_closed,
                spider=spider,
                reason=reason,
            )
        except Exception:
            log_failure("Error while sending spider_close signal")

        assert self.crawler.stats
        try:
            if argument_is_required(self.crawler.stats.close_spider, "spider"):
                warnings.warn(
                    f"The close_spider() method of {global_object_name(type(self.crawler.stats))} requires a spider argument,"
                    f" this is deprecated and the argument will not be passed in future Scrapy versions.",
                    ScrapyDeprecationWarning,
                    stacklevel=2,
                )
                self.crawler.stats.close_spider(
                    spider=self.crawler.spider, reason=reason
                )
            else:
                self.crawler.stats.close_spider(reason=reason)
        except Exception:
            log_failure("Stats close failure")

        logger.info(
            "Spider closed (%(reason)s)",
            {"reason": reason},
            extra={"spider": spider},
        )

        self._slot = None
        self.spider = None

        try:
            await ensure_awaitable(self._spider_closed_callback(spider))
        except Exception:
            log_failure("Error running spider_closed_callback")