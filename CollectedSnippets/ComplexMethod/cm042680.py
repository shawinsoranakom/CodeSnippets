def scraped_data(
        self,
        args: tuple[
            list[Any], list[Request], argparse.Namespace, int, Spider, CallbackT
        ],
    ) -> list[Any]:
        items, requests, opts, depth, spider, callback = args
        if opts.pipelines:
            assert self.pcrawler.engine
            itemproc = self.pcrawler.engine.scraper.itemproc
            if hasattr(itemproc, "process_item_async"):
                for item in items:
                    _schedule_coro(itemproc.process_item_async(item))
            else:
                for item in items:
                    itemproc.process_item(item, spider)
        self.add_items(depth, items)
        self.add_requests(depth, requests)

        scraped_data = items if opts.output else []
        if depth < opts.depth:
            for req in requests:
                req.meta["_depth"] = depth + 1
                req.meta["_callback"] = req.callback
                req.callback = callback
            scraped_data += requests

        return scraped_data