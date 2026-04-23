def test_buffer_overflow_and_cleanup(self):
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

        # Verify that some items are still accessible
        accessible_count = 0
        for key, original_value, address, monotonic_id in stored_items:
            for i in range(self.storage.n_readers):
                retrieved = self.storage.get(address, monotonic_id)
            if retrieved == original_value:
                accessible_count += 1

        self.assertEqual(accessible_count, len(stored_items))

        try:
            for i in range(len(stored_items), 1000):  # Try to store many items
                key = f"item_{i}"
                value = f"data_{i}" * 100  # Make it reasonably sized
                address, monotonic_id = self.storage.put(key, value)
                stored_items.append((key, value, address, monotonic_id))
        except MemoryError:
            print(f"Buffer filled after {len(stored_items)} items")

        # Verify that some items are still accessibles
        for key, original_value, address, monotonic_id in stored_items:
            try:
                for i in range(self.storage.n_readers):
                    retrieved = self.storage.get(address, monotonic_id)
                if retrieved == original_value:
                    accessible_count += 1
            except ValueError as e:
                print(f"Error retrieving {key}: {e}")

        # some items from the first batch may still be accessible
        self.assertGreaterEqual(accessible_count, len(stored_items))