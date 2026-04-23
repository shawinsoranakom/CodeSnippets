def test_meta(self):
        spider = DemoSpider()

        # extract contracts correctly
        contracts = self.conman.extract_contracts(spider.returns_request_meta)
        assert len(contracts) == 3
        assert frozenset(type(x) for x in contracts) == frozenset(
            [UrlContract, MetadataContract, ReturnsContract]
        )

        contracts = self.conman.extract_contracts(spider.returns_item_meta)
        assert len(contracts) == 3
        assert frozenset(type(x) for x in contracts) == frozenset(
            [UrlContract, MetadataContract, ReturnsContract]
        )

        response = ResponseMetaMock()

        # returns_request
        request = self.conman.from_method(spider.returns_request_meta, self.results)
        assert request.meta["cookiejar"] == "session1"
        response.meta = request.meta
        request.callback(response)
        assert response.meta["cookiejar"] == "session1"
        self.should_succeed()

        response = ResponseMetaMock()

        # returns_item
        request = self.conman.from_method(spider.returns_item_meta, self.results)
        assert request.meta["key"] == "example"
        response.meta = request.meta
        request.callback(ResponseMetaMock)
        assert response.meta["key"] == "example"
        self.should_succeed()

        response = ResponseMetaMock()

        request = self.conman.from_method(
            spider.returns_error_missing_meta, self.results
        )
        request.callback(response)
        self.should_error()