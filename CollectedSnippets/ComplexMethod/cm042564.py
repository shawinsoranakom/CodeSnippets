async def test_generator_output_chain(self):
        """
        (4) An exception from a middleware's process_spider_output method should be sent
        to the process_spider_exception method from the next middleware in the chain.
        The result of the recovery by the process_spider_exception method should be handled
        by the process_spider_output method from the next middleware.
        The final item count should be 2 (one from the spider callback and one from the
        process_spider_exception chain)
        """
        log4 = await self.crawl_log(GeneratorOutputChainSpider)
        assert "'item_scraped_count': 2" in str(log4)
        assert (
            "GeneratorRecoverMiddleware.process_spider_exception: LookupError caught"
            in str(log4)
        )
        assert (
            "GeneratorDoNothingAfterFailureMiddleware.process_spider_exception: LookupError caught"
            in str(log4)
        )
        assert (
            "GeneratorFailMiddleware.process_spider_exception: LookupError caught"
            not in str(log4)
        )
        assert (
            "GeneratorDoNothingAfterRecoveryMiddleware.process_spider_exception: LookupError caught"
            not in str(log4)
        )
        item_from_callback = {
            "processed": [
                "parse-first-item",
                "GeneratorFailMiddleware.process_spider_output",
                "GeneratorDoNothingAfterFailureMiddleware.process_spider_output",
                "GeneratorRecoverMiddleware.process_spider_output",
                "GeneratorDoNothingAfterRecoveryMiddleware.process_spider_output",
            ]
        }
        item_recovered = {
            "processed": [
                "GeneratorRecoverMiddleware.process_spider_exception",
                "GeneratorDoNothingAfterRecoveryMiddleware.process_spider_output",
            ]
        }
        assert str(item_from_callback) in str(log4)
        assert str(item_recovered) in str(log4)
        assert "parse-second-item" not in str(log4)