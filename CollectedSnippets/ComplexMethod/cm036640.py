def test_blocking_unread_object(self):
        """Test behavior when buffer fills up and needs cleanup."""
        # Fill up the buffer with many small objects
        stored_items = []

        try:
            for i in range(1000):  # Try to store many items
                key = f"item_{i}"
                value = f"data_{i}" * 100  # Make it reasonably sized
                address, monotonic_id = self.storage.put(key, value)
                stored_items.append((key, value, address, monotonic_id))
        except MemoryError:
            print(f"Buffer filled after {len(stored_items)} items")

        # read all items except the first one
        # to simulate a blocking situation
        accessible_count = 0
        for key, original_value, address, monotonic_id in stored_items[1:]:
            for i in range(self.storage.n_readers):
                retrieved = self.storage.get(address, monotonic_id)
            if retrieved == original_value:
                accessible_count += 1

        self.assertEqual(accessible_count, len(stored_items) - 1)

        try:
            key = f"item_{len(stored_items)}"
            value = f"data_{len(stored_items)}" * 100
            address, monotonic_id = self.storage.put(key, value)
        except MemoryError:
            print(f"Buffer filled after {len(stored_items)} items")

        # read the first item
        for i in range(self.storage.n_readers):
            key, original_value, address, monotonic_id = stored_items[0]
            retrieved = self.storage.get(address, monotonic_id)
            self.assertEqual(retrieved, original_value)

        try:
            for i in range(len(stored_items), 1000):  # Try to store many items
                key = f"item_{i}"
                value = f"data_{i}" * 100  # Make it reasonably sized
                address, monotonic_id = self.storage.put(key, value)
                stored_items.append((key, value, address, monotonic_id))
        except MemoryError:
            print(f"Buffer filled after {len(stored_items)} items")

        # some items from the first batch may still be accessible
        self.assertGreaterEqual(len(stored_items), accessible_count + 10)