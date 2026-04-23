def test_selector(self):
        body = b"<html><head><title>Some page</title><body></body></html>"
        response = self.response_class("http://www.example.com", body=body)

        assert isinstance(response.selector, Selector)
        assert response.selector.type == "html"
        assert response.selector is response.selector  # property is cached
        assert response.selector.response is response

        assert response.selector.xpath("//title/text()").getall() == ["Some page"]
        assert response.selector.css("title::text").getall() == ["Some page"]
        assert response.selector.re("Some (.*)</title>") == ["page"]