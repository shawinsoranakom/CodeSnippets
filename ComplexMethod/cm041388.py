def test_no_limits(self, max_count, max_window):
        if max_count or max_window:
            batcher = Batcher(max_count=max_count, max_window=max_window)
        else:
            batcher = Batcher()

        assert batcher.is_triggered()  # no limit always returns true

        assert batcher.add("item1")
        assert batcher.get_current_size() == 1
        assert batcher.is_triggered()

        assert batcher.add(["item2", "item3"])
        assert batcher.get_current_size() == 3
        assert batcher.is_triggered()

        result = batcher.flush()
        assert result == ["item1", "item2", "item3"]
        assert batcher.get_current_size() == 0