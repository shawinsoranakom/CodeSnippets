def test_source_on_flat_fields_from_sibling(self):
        """source on individual fields targeting data in sibling div."""
        schema = {
            "name": "Items",
            "baseSelector": "//div[@class='item']",
            "fields": [
                {"name": "name", "selector": ".//span[@class='name']", "type": "text"},
                {"name": "price", "selector": ".//span[@class='price']", "type": "text", "source": "+ div.details"},
                {"name": "stock", "selector": ".//span[@class='stock']", "type": "text", "source": "+ div.details"},
            ],
        }
        strategy = JsonXPathExtractionStrategy(schema)
        results = strategy.extract(None, NESTED_SIBLING_HTML)
        assert len(results) == 2
        assert results[0]["name"] == "Item A"
        assert results[0]["price"] == "$10"
        assert results[0]["stock"] == "In Stock"
        assert results[1]["name"] == "Item B"
        assert results[1]["price"] == "$20"
        assert results[1]["stock"] == "Out of Stock"