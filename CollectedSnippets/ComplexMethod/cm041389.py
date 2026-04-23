def test_triggered_state(self):
        batcher = Batcher(max_count=2)

        assert not batcher.add("item1")
        assert not batcher.is_triggered()

        assert batcher.add("item2")
        assert batcher.is_triggered()

        assert batcher.add("item3")
        assert batcher.flush() == ["item1", "item2", "item3"]
        assert batcher.get_current_size() == 0
        assert not batcher.is_triggered()