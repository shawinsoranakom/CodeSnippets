def _assert_signals_caught(run: CrawlerRun) -> None:
        assert signals.engine_started in run.signals_caught
        assert signals.engine_stopped in run.signals_caught
        assert signals.spider_opened in run.signals_caught
        assert signals.spider_idle in run.signals_caught
        assert signals.spider_closed in run.signals_caught
        assert signals.headers_received in run.signals_caught

        assert {"spider": run.crawler.spider} == run.signals_caught[
            signals.spider_opened
        ]
        assert {"spider": run.crawler.spider} == run.signals_caught[signals.spider_idle]
        assert {
            "spider": run.crawler.spider,
            "reason": "finished",
        } == run.signals_caught[signals.spider_closed]