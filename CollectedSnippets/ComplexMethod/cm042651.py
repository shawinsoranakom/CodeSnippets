def test_url_is_from_spider_with_allowed_domains():
    class MySpider(Spider):
        name = "example.com"
        allowed_domains = ["example.org", "example.net"]

    assert url_is_from_spider("http://www.example.com/some/page.html", MySpider)
    assert url_is_from_spider("http://sub.example.com/some/page.html", MySpider)
    assert url_is_from_spider("http://example.com/some/page.html", MySpider)
    assert url_is_from_spider("http://www.example.org/some/page.html", MySpider)
    assert url_is_from_spider("http://www.example.net/some/page.html", MySpider)
    assert not url_is_from_spider("http://www.example.us/some/page.html", MySpider)

    class MySpider2(Spider):
        name = "example.com"
        allowed_domains = {"example.com", "example.net"}

    assert url_is_from_spider("http://www.example.com/some/page.html", MySpider2)

    class MySpider3(Spider):
        name = "example.com"
        allowed_domains = ("example.com", "example.net")

    assert url_is_from_spider("http://www.example.com/some/page.html", MySpider3)