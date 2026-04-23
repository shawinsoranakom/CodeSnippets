def _assert_items_error(run: CrawlerRun) -> None:
        assert len(run.itemerror) == 2
        for item, response, spider, failure in run.itemerror:
            assert failure.value.__class__ is ZeroDivisionError
            assert spider == run.crawler.spider

            assert item["url"] == response.url
            if "item1.html" in item["url"]:
                assert item["name"] == "Item 1 name"
                assert item["price"] == "100"
            if "item2.html" in item["url"]:
                assert item["name"] == "Item 2 name"
                assert item["price"] == "200"