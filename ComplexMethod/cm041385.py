def test_max_count_limit(self):
        batcher = Batcher(max_count=3)

        assert not batcher.add("item1")
        assert not batcher.add("item2")
        assert batcher.add("item3")

        assert batcher.is_triggered()
        assert batcher.get_current_size() == 3

        result = batcher.flush()
        assert result == ["item1", "item2", "item3"]
        assert batcher.get_current_size() == 0

        assert not batcher.add("item4")
        assert not batcher.add("item5")
        assert batcher.get_current_size() == 2