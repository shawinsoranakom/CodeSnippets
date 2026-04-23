def test_add_single_item(self):
        batcher = Batcher(max_count=2)

        assert not batcher.add("item1")
        assert batcher.get_current_size() == 1
        assert not batcher.is_triggered()

        assert batcher.add("item2")
        assert batcher.is_triggered()

        result = batcher.flush()
        assert result == ["item1", "item2"]
        assert batcher.get_current_size() == 0