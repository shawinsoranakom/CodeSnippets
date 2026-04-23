def _assert_scraped_items(run: CrawlerRun) -> None:
        assert len(run.itemresp) == 2
        for item_, response in run.itemresp:
            item = ItemAdapter(item_)
            assert item["url"] == response.url
            if "item1.html" in item["url"]:
                assert item["name"] == "Item 1 name"
                assert item["price"] == "100"
            if "item2.html" in item["url"]:
                assert item["name"] == "Item 2 name"
                assert item["price"] == "200"