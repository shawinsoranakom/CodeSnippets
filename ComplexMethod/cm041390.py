def test_max_count_partial_flush(self):
        batcher = Batcher(max_count=2)

        assert batcher.add(["item1", "item2", "item3", "item4"])
        assert batcher.is_triggered()

        assert batcher.flush(partial=True) == ["item1", "item2"]
        assert batcher.get_current_size() == 2

        assert batcher.flush(partial=True) == ["item3", "item4"]
        assert not batcher.is_triggered()  # early flush

        assert batcher.flush() == []
        assert batcher.get_current_size() == 0
        assert not batcher.is_triggered()