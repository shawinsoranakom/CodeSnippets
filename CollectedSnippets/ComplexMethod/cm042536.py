def test_cb_kwargs(self):
        spider = DemoSpider()
        response = ResponseMock()

        # extract contracts correctly
        contracts = self.conman.extract_contracts(spider.returns_request_cb_kwargs)
        assert len(contracts) == 3
        assert frozenset(type(x) for x in contracts) == frozenset(
            [UrlContract, CallbackKeywordArgumentsContract, ReturnsContract]
        )

        contracts = self.conman.extract_contracts(spider.returns_item_cb_kwargs)
        assert len(contracts) == 3
        assert frozenset(type(x) for x in contracts) == frozenset(
            [UrlContract, CallbackKeywordArgumentsContract, ReturnsContract]
        )

        contracts = self.conman.extract_contracts(
            spider.returns_item_cb_kwargs_error_unexpected_keyword
        )
        assert len(contracts) == 3
        assert frozenset(type(x) for x in contracts) == frozenset(
            [UrlContract, CallbackKeywordArgumentsContract, ReturnsContract]
        )

        contracts = self.conman.extract_contracts(
            spider.returns_item_cb_kwargs_error_missing_argument
        )
        assert len(contracts) == 2
        assert frozenset(type(x) for x in contracts) == frozenset(
            [UrlContract, ReturnsContract]
        )

        # returns_request
        request = self.conman.from_method(
            spider.returns_request_cb_kwargs, self.results
        )
        request.callback(response, **request.cb_kwargs)
        self.should_succeed()

        # returns_item
        request = self.conman.from_method(spider.returns_item_cb_kwargs, self.results)
        request.callback(response, **request.cb_kwargs)
        self.should_succeed()

        # returns_item (error, callback doesn't take keyword arguments)
        request = self.conman.from_method(
            spider.returns_item_cb_kwargs_error_unexpected_keyword, self.results
        )
        request.callback(response, **request.cb_kwargs)
        self.should_error()

        # returns_item (error, contract doesn't provide keyword arguments)
        request = self.conman.from_method(
            spider.returns_item_cb_kwargs_error_missing_argument, self.results
        )
        request.callback(response, **request.cb_kwargs)
        self.should_error()