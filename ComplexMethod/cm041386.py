def test_max_window_limit(self):
        max_window = 0.5
        batcher = Batcher(max_window=max_window)

        assert not batcher.add("item1")
        assert batcher.get_current_size() == 1
        assert not batcher.is_triggered()

        assert not batcher.add("item2")
        assert batcher.get_current_size() == 2
        assert not batcher.is_triggered()

        time.sleep(max_window + 0.1)

        assert batcher.add("item3")
        assert batcher.is_triggered()
        assert batcher.get_current_size() == 3

        result = batcher.flush()
        assert result == ["item1", "item2", "item3"]
        assert batcher.get_current_size() == 0