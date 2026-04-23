def test_basic_source_extraction(self):
        """Fields with source='+ tr' should extract data from the next sibling row."""
        schema = {
            "name": "HN",
            "baseSelector": "tr.athing.submission",
            "fields": [
                {"name": "rank", "selector": "span.rank", "type": "text"},
                {"name": "title", "selector": "span.titleline a", "type": "text"},
                {"name": "url", "selector": "span.titleline a", "type": "attribute", "attribute": "href"},
                {"name": "score", "selector": "span.score", "type": "text", "source": "+ tr"},
                {"name": "author", "selector": "a.hnuser", "type": "text", "source": "+ tr"},
            ],
        }
        results = self._extract(schema)
        assert len(results) == 2

        assert results[0]["rank"] == "1."
        assert results[0]["title"] == "Alpha"
        assert results[0]["url"] == "https://example.com/a"
        assert results[0]["score"] == "100 points"
        assert results[0]["author"] == "alice"

        assert results[1]["rank"] == "2."
        assert results[1]["title"] == "Beta"
        assert results[1]["score"] == "42 points"
        assert results[1]["author"] == "bob"