def __init__(self, crawler: Crawler):
        self.crawler: Crawler = crawler

        # for CLOSESPIDER_TIMEOUT
        self.task: CallLaterResult | None = None

        # for CLOSESPIDER_TIMEOUT_NO_ITEM
        self.task_no_item: AsyncioLoopingCall | LoopingCall | None = None

        self.close_on: dict[str, Any] = {
            "timeout": crawler.settings.getfloat("CLOSESPIDER_TIMEOUT"),
            "itemcount": crawler.settings.getint("CLOSESPIDER_ITEMCOUNT"),
            "pagecount": crawler.settings.getint("CLOSESPIDER_PAGECOUNT"),
            "errorcount": crawler.settings.getint("CLOSESPIDER_ERRORCOUNT"),
            "timeout_no_item": crawler.settings.getint("CLOSESPIDER_TIMEOUT_NO_ITEM"),
            "pagecount_no_item": crawler.settings.getint(
                "CLOSESPIDER_PAGECOUNT_NO_ITEM"
            ),
        }

        if not any(self.close_on.values()):
            raise NotConfigured

        self.counter: defaultdict[str, int] = defaultdict(int)

        if self.close_on.get("errorcount"):
            crawler.signals.connect(self.error_count, signal=signals.spider_error)
        if self.close_on.get("pagecount") or self.close_on.get("pagecount_no_item"):
            crawler.signals.connect(self.page_count, signal=signals.response_received)
        if self.close_on.get("timeout"):
            crawler.signals.connect(self.spider_opened, signal=signals.spider_opened)
        if self.close_on.get("itemcount") or self.close_on.get("pagecount_no_item"):
            crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)
        if self.close_on.get("timeout_no_item"):
            self.timeout_no_item: int = self.close_on["timeout_no_item"]
            self.items_in_period: int = 0
            crawler.signals.connect(
                self.spider_opened_no_item, signal=signals.spider_opened
            )
            crawler.signals.connect(
                self.item_scraped_no_item, signal=signals.item_scraped
            )

        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)