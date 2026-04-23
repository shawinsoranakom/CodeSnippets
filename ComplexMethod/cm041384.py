def test_add_multiple_items(self):
        batcher = Batcher(max_count=3)

        assert not batcher.add(["item1", "item2"])
        assert batcher.get_current_size() == 2
        assert not batcher.is_triggered()

        assert batcher.add(["item3", "item4"])  # exceeds max_count
        assert batcher.is_triggered()
        assert batcher.get_current_size() == 4

        result = batcher.flush()
        assert result == ["item1", "item2", "item3", "item4"]
        assert batcher.get_current_size() == 0

        assert batcher.add(["item1", "item2", "item3", "item4"])
        assert batcher.flush() == ["item1", "item2", "item3", "item4"]
        assert not batcher.is_triggered()