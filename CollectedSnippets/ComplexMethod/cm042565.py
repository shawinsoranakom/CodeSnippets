async def test_not_a_generator_output_chain(self):
        """
        (5) An exception from a middleware's process_spider_output method should be sent
        to the process_spider_exception method from the next middleware in the chain.
        The result of the recovery by the process_spider_exception method should be handled
        by the process_spider_output method from the next middleware.
        The final item count should be 1 (from the process_spider_exception chain, the items
        from the spider callback are lost)
        """
        log5 = await self.crawl_log(NotGeneratorOutputChainSpider)
        assert "'item_scraped_count': 1" in str(log5)
        assert (
            "GeneratorRecoverMiddleware.process_spider_exception: ReferenceError caught"
            in str(log5)
        )
        assert (
            "GeneratorDoNothingAfterFailureMiddleware.process_spider_exception: ReferenceError caught"
            in str(log5)
        )
        assert (
            "GeneratorFailMiddleware.process_spider_exception: ReferenceError caught"
            not in str(log5)
        )
        assert (
            "GeneratorDoNothingAfterRecoveryMiddleware.process_spider_exception: ReferenceError caught"
            not in str(log5)
        )
        item_recovered = {
            "processed": [
                "NotGeneratorRecoverMiddleware.process_spider_exception",
                "NotGeneratorDoNothingAfterRecoveryMiddleware.process_spider_output",
            ]
        }
        assert str(item_recovered) in str(log5)
        assert "parse-first-item" not in str(log5)
        assert "parse-second-item" not in str(log5)