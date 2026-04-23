def test_concurrent_port_allocation_stress_test(self):
        """Stress test concurrent port allocation."""
        allocated_ports = []
        port_locks = []
        errors = []

        def worker_allocate_port(worker_id):
            """Worker function that allocates a port."""
            try:
                result = find_available_port_with_lock(
                    min_port=31000,
                    max_port=31020,  # Small range to force contention
                    max_attempts=10,
                    bind_address='0.0.0.0',
                    lock_timeout=3.0,
                )

                if result:
                    port, lock = result
                    allocated_ports.append((worker_id, port))
                    port_locks.append(lock)
                    # Simulate work
                    time.sleep(0.05)
                    return port
                else:
                    errors.append(f'Worker {worker_id}: No port available')
                    return None

            except Exception as e:
                errors.append(f'Worker {worker_id}: {str(e)}')
                return None

        # Run many workers concurrently
        num_workers = 15
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(worker_allocate_port, i): i for i in range(num_workers)
            }
            results = {}
            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    result = future.result()
                    results[worker_id] = result
                except Exception as e:
                    errors.append(f'Worker {worker_id} exception: {str(e)}')

        # Analyze results
        successful_allocations = [
            (wid, port) for wid, port in allocated_ports if port is not None
        ]
        allocated_port_numbers = [port for _, port in successful_allocations]

        print(f'Successful allocations: {len(successful_allocations)}')
        print(f'Allocated ports: {allocated_port_numbers}')
        print(f'Errors: {len(errors)}')
        if errors:
            print(f'Error details: {errors[:5]}')  # Show first 5 errors

        # Verify no duplicate ports
        unique_ports = set(allocated_port_numbers)
        assert len(allocated_port_numbers) == len(unique_ports), (
            f'Duplicate ports found: {allocated_port_numbers}'
        )

        # Clean up locks
        for lock in port_locks:
            if lock:
                lock.release()