def test_multiple_policies(self):
        batcher = Batcher(max_count=5, max_window=2.0)

        item1 = SimpleItem(1)
        for _ in range(5):
            batcher.add(item1)
        assert batcher.is_triggered()

        result = batcher.flush()
        assert result == [item1, item1, item1, item1, item1]
        assert batcher.get_current_size() == 0

        batcher.add(item1)
        assert not batcher.is_triggered()

        item2 = SimpleItem(10)

        time.sleep(2.1)
        batcher.add(item2)
        assert batcher.is_triggered()

        result = batcher.flush()
        assert result == [item1, item2]