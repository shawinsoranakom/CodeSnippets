async def test_spider_custom_settings_log_level(self, tmp_path):
        log_file = Path(tmp_path, "log.txt")
        log_file.write_text("previous message\n", encoding="utf-8")

        info_count = None

        class MySpider(scrapy.Spider):
            name = "spider"
            custom_settings = {
                "LOG_LEVEL": "INFO",
                "LOG_FILE": str(log_file),
            }

            async def start(self):
                info_count_start = crawler.stats.get_value("log_count/INFO")
                logging.debug("debug message")  # noqa: LOG015
                logging.info("info message")  # noqa: LOG015
                logging.warning("warning message")  # noqa: LOG015
                logging.error("error message")  # noqa: LOG015
                nonlocal info_count
                info_count = (
                    crawler.stats.get_value("log_count/INFO") - info_count_start
                )
                return
                yield

        try:
            configure_logging()
            assert get_scrapy_root_handler().level == logging.DEBUG
            crawler = get_crawler(MySpider)
            assert get_scrapy_root_handler().level == logging.INFO
            await crawler.crawl_async()
        finally:
            _uninstall_scrapy_root_handler()

        logged = log_file.read_text(encoding="utf-8")

        assert "previous message" in logged
        assert "debug message" not in logged
        assert "info message" in logged
        assert "warning message" in logged
        assert "error message" in logged
        assert crawler.stats.get_value("log_count/ERROR") == 1
        assert crawler.stats.get_value("log_count/WARNING") == 1
        assert info_count == 1
        assert crawler.stats.get_value("log_count/DEBUG", 0) == 0