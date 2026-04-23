def _check_deprecated_start_requests_use(self) -> None:
        start_requests_cls = None
        start_cls = None
        spidercls = self._spider.__class__
        mro = spidercls.__mro__

        for cls in mro:
            cls_dict = cls.__dict__
            if start_requests_cls is None and "start_requests" in cls_dict:
                start_requests_cls = cls
            if start_cls is None and "start" in cls_dict:
                start_cls = cls
            if start_requests_cls is not None and start_cls is not None:
                break

        # Spider defines both, start_requests and start.
        assert start_requests_cls is not None
        assert start_cls is not None

        if (
            start_requests_cls is not Spider
            and start_cls is not start_requests_cls
            and mro.index(start_requests_cls) < mro.index(start_cls)
        ):
            src = global_object_name(start_requests_cls)
            if start_requests_cls is not spidercls:
                src += f" (inherited by {global_object_name(spidercls)})"
            warn(
                f"{src} defines the deprecated start_requests() method. "
                f"start_requests() has been deprecated in favor of a new "
                f"method, start(), to support asynchronous code "
                f"execution. start_requests() will stop being called in a "
                f"future version of Scrapy. If you use Scrapy 2.13 or "
                f"higher only, replace start_requests() with start(); "
                f"note that start() is a coroutine (async def). If you "
                f"need to maintain compatibility with lower Scrapy versions, "
                f"when overriding start_requests() in a spider class, "
                f"override start() as well; you can use super() to "
                f"reuse the inherited start() implementation without "
                f"copy-pasting. See the release notes of Scrapy 2.13 for "
                f"details: https://docs.scrapy.org/en/2.13/news.html",
                ScrapyDeprecationWarning,
                stacklevel=2,
            )

        if (
            self._use_start_requests
            and start_cls is not Spider
            and start_requests_cls is not start_cls
            and mro.index(start_cls) < mro.index(start_requests_cls)
        ):
            src = global_object_name(start_cls)
            if start_cls is not spidercls:
                src += f" (inherited by {global_object_name(spidercls)})"
            raise ValueError(
                f"{src} does not define the deprecated start_requests() "
                f"method. However, one or more of your enabled spider "
                f"middlewares (reported in an earlier deprecation warning) "
                f"define the process_start_requests() method, and not the "
                f"process_start() method, making them only compatible with "
                f"(deprecated) spiders that define the start_requests() "
                f"method. To solve this issue, disable the offending spider "
                f"middlewares, upgrade them as described in that earlier "
                f"deprecation warning, or make your spider compatible with "
                f"deprecated spider middlewares (and earlier Scrapy versions) "
                f"by defining a sync start_requests() method that works "
                f"similarly to its existing start() method. See the "
                f"release notes of Scrapy 2.13 for details: "
                f"https://docs.scrapy.org/en/2.13/news.html"
            )