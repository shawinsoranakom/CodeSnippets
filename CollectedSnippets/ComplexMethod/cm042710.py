def _check_deprecated_process_start_requests_use(
        self, middlewares: tuple[Any, ...]
    ) -> None:
        deprecated_middlewares = [
            middleware
            for middleware in middlewares
            if hasattr(middleware, "process_start_requests")
            and not hasattr(middleware, "process_start")
        ]
        modern_middlewares = [
            middleware
            for middleware in middlewares
            if not hasattr(middleware, "process_start_requests")
            and hasattr(middleware, "process_start")
        ]
        if deprecated_middlewares and modern_middlewares:
            raise ValueError(
                "You are trying to combine spider middlewares that only "
                "define the deprecated process_start_requests() method () "
                "with spider middlewares that only define the "
                "process_start() method (). This is not possible. You must "
                "either disable or make universal 1 of those 2 sets of "
                "spider middlewares. Making a spider middleware universal "
                "means having it define both methods. See the release notes "
                "of Scrapy 2.13 for details: "
                "https://docs.scrapy.org/en/2.13/news.html"
            )

        self._use_start_requests = bool(deprecated_middlewares)
        if self._use_start_requests:
            deprecated_middleware_list = ", ".join(
                global_object_name(middleware.__class__)
                for middleware in deprecated_middlewares
            )
            warn(
                f"The following enabled spider middlewares, directly or "
                f"through their parent classes, define the deprecated "
                f"process_start_requests() method: "
                f"{deprecated_middleware_list}. process_start_requests() has "
                f"been deprecated in favor of a new method, process_start(), "
                f"to support asynchronous code execution. "
                f"process_start_requests() will stop being called in a future "
                f"version of Scrapy. If you use Scrapy 2.13 or higher "
                f"only, replace process_start_requests() with "
                f"process_start(); note that process_start() is a coroutine "
                f"(async def). If you need to maintain compatibility with "
                f"lower Scrapy versions, when defining "
                f"process_start_requests() in a spider middleware class, "
                f"define process_start() as well. See the release notes of "
                f"Scrapy 2.13 for details: "
                f"https://docs.scrapy.org/en/2.13/news.html",
                ScrapyDeprecationWarning,
                stacklevel=2,
            )