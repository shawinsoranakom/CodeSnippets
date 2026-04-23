async def start_itemproc_async(
        self, item: Any, *, response: Response | Failure | None
    ) -> None:
        """Send *item* to the item pipelines for processing.

        *response* is the source of the item data. If the item does not come
        from response data, e.g. it was hard-coded, set it to ``None``.

        .. versionadded:: 2.14
        """
        assert self.slot is not None  # typing
        assert self.crawler.spider is not None  # typing
        self.slot.itemproc_size += 1
        try:
            if self._itemproc_has_async["process_item"]:
                output = await self.itemproc.process_item_async(item)
            else:
                output = await maybe_deferred_to_future(
                    self.itemproc.process_item(item, self.crawler.spider)
                )
        except DropItem as ex:
            logkws = self.logformatter.dropped(item, ex, response, self.crawler.spider)
            if logkws is not None:
                logger.log(
                    *logformatter_adapter(logkws), extra={"spider": self.crawler.spider}
                )
            await self.signals.send_catch_log_async(
                signal=signals.item_dropped,
                item=item,
                response=response,
                spider=self.crawler.spider,
                exception=ex,
            )
        except Exception as ex:
            logkws = self.logformatter.item_error(
                item, ex, response, self.crawler.spider
            )
            logger.log(
                *logformatter_adapter(logkws),
                extra={"spider": self.crawler.spider},
                exc_info=True,
            )
            await self.signals.send_catch_log_async(
                signal=signals.item_error,
                item=item,
                response=response,
                spider=self.crawler.spider,
                failure=Failure(),
            )
        else:
            logkws = self.logformatter.scraped(output, response, self.crawler.spider)
            if logkws is not None:
                logger.log(
                    *logformatter_adapter(logkws), extra={"spider": self.crawler.spider}
                )
            await self.signals.send_catch_log_async(
                signal=signals.item_scraped,
                item=output,
                response=response,
                spider=self.crawler.spider,
            )
        finally:
            self.slot.itemproc_size -= 1