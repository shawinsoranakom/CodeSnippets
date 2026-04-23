async def test_log_delta(self):
        def emulate(
            settings: dict[str, Any] | None = None,
        ) -> tuple[PeriodicLog, dict[str, Any], dict[str, Any]]:
            spider = MetaSpider()
            ext = extension(settings)
            ext.spider_opened(spider)
            ext.set_a()
            a = ext.log_delta()
            ext.set_b()
            b = ext.log_delta()
            ext.spider_closed(spider, reason="finished")
            return ext, a, b

        def check(settings: dict[str, Any], condition: Callable) -> None:
            ext, a, b = emulate(settings)
            assert list(a["delta"].keys()) == [
                k for k, v in ext.stats._stats.items() if condition(k, v)
            ]
            assert list(b["delta"].keys()) == [
                k for k, v in ext.stats._stats.items() if condition(k, v)
            ]

        # Including all
        check({"PERIODIC_LOG_DELTA": True}, lambda k, v: isinstance(v, (int, float)))

        # include:
        check(
            {"PERIODIC_LOG_DELTA": {"include": ["downloader/"]}},
            lambda k, v: isinstance(v, (int, float)) and "downloader/" in k,
        )

        # include multiple
        check(
            {"PERIODIC_LOG_DELTA": {"include": ["downloader/", "scheduler/"]}},
            lambda k, v: (
                isinstance(v, (int, float))
                and ("downloader/" in k or "scheduler/" in k)
            ),
        )

        # exclude
        check(
            {"PERIODIC_LOG_DELTA": {"exclude": ["downloader/"]}},
            lambda k, v: isinstance(v, (int, float)) and "downloader/" not in k,
        )

        # exclude multiple
        check(
            {"PERIODIC_LOG_DELTA": {"exclude": ["downloader/", "scheduler/"]}},
            lambda k, v: (
                isinstance(v, (int, float))
                and ("downloader/" not in k and "scheduler/" not in k)
            ),
        )

        # include exclude combined
        check(
            {"PERIODIC_LOG_DELTA": {"include": ["downloader/"], "exclude": ["bytes"]}},
            lambda k, v: (
                isinstance(v, (int, float))
                and ("downloader/" in k and "bytes" not in k)
            ),
        )