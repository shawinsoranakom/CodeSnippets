def test_matches(self):
            url1 = "http://lotsofstuff.com/stuff1/index"
            url2 = "http://evenmorestuff.com/uglystuff/index"

            lx = self.extractor_cls(allow=(r"stuff1",))
            assert lx.matches(url1)
            assert not lx.matches(url2)

            lx = self.extractor_cls(deny=(r"uglystuff",))
            assert lx.matches(url1)
            assert not lx.matches(url2)

            lx = self.extractor_cls(allow_domains=("evenmorestuff.com",))
            assert not lx.matches(url1)
            assert lx.matches(url2)

            lx = self.extractor_cls(deny_domains=("lotsofstuff.com",))
            assert not lx.matches(url1)
            assert lx.matches(url2)

            lx = self.extractor_cls(
                allow=["blah1"],
                deny=["blah2"],
                allow_domains=["blah1.com"],
                deny_domains=["blah2.com"],
            )
            assert lx.matches("http://blah1.com/blah1")
            assert not lx.matches("http://blah1.com/blah2")
            assert not lx.matches("http://blah2.com/blah1")
            assert not lx.matches("http://blah2.com/blah2")