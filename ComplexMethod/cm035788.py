def test_port_lock_prevents_duplicate_allocation(self):
        """Test that port locking prevents duplicate port allocation."""
        allocated_ports = []
        port_locks = []

        def allocate_port():
            """Simulate port allocation by multiple workers."""
            result = find_available_port_with_lock(
                min_port=30000,
                max_port=30010,  # Small range to force conflicts
                max_attempts=5,
                bind_address='0.0.0.0',
                lock_timeout=2.0,
            )

            if result:
                port, lock = result
                allocated_ports.append(port)
                port_locks.append(lock)
                # Simulate some work time
                time.sleep(0.1)
                return port
            return None

        # Run multiple threads concurrently
        num_workers = 8
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(allocate_port) for _ in range(num_workers)]
            results = [future.result() for future in as_completed(futures)]

        # Filter out None results
        successful_ports = [port for port in results if port is not None]

        # Verify no duplicate ports were allocated
        assert len(successful_ports) == len(set(successful_ports)), (
            f'Duplicate ports allocated: {successful_ports}'
        )

        # Clean up locks
        for lock in port_locks:
            if lock:
                lock.release()

        print(
            f'Successfully allocated {len(successful_ports)} unique ports: {successful_ports}'
        )