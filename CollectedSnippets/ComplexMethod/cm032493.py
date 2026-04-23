def test_load_from_state_builds_documents(monkeypatch):
    monkeypatch.setattr("common.data_source.rss_connector.requests.get", lambda *_args, **_kwargs: _FakeResponse())
    monkeypatch.setattr(
        "common.data_source.rss_connector.feedparser.parse",
        lambda _content: _mock_feed(
            {
                "id": "entry-1",
                "link": "https://example.com/posts/1",
                "title": "Post One",
                "content": [{"value": "<p>Hello <b>world</b></p>"}],
                "author": "Alice",
                "tags": [{"term": "news"}, {"term": "product"}],
                "updated": "Tue, 02 Jan 2024 15:04:05 GMT",
            }
        ),
    )

    connector = RSSConnector(feed_url="https://example.com/feed.xml")
    batch = next(connector.load_from_state())

    assert len(batch) == 1
    doc = batch[0]
    assert doc.source == DocumentSource.RSS
    assert doc.semantic_identifier == "Post One"
    assert doc.extension == ".txt"
    assert doc.metadata == {
        "feed_url": "https://example.com/feed.xml",
        "link": "https://example.com/posts/1",
        "author": "Alice",
        "categories": ["news", "product"],
    }
    assert "Hello" in doc.blob.decode("utf-8")
    assert "world" in doc.blob.decode("utf-8")