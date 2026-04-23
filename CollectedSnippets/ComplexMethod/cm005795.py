def test_log_buffer_thread_safety(self):
        """Test that log buffer operations are thread-safe."""
        import threading
        import time

        buffer = SizedLogBuffer(max_readers=5)
        buffer.max = 100

        results = []
        errors = []

        def write_logs():
            try:
                for i in range(10):
                    message = json.dumps({"event": f"Thread message {i}", "timestamp": time.time() + i})
                    buffer.write(message)
                    time.sleep(0.001)  # Small delay to simulate real usage
                results.append("write_success")
            except Exception as e:
                errors.append(f"Write error: {e}")

        def read_logs():
            try:
                for _i in range(5):
                    entries = buffer.get_last_n(5)
                    assert isinstance(entries, dict)
                    time.sleep(0.002)  # Small delay
                results.append("read_success")
            except Exception as e:
                errors.append(f"Read error: {e}")

        # Create multiple threads for reading and writing
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=write_logs, daemon=False))
            threads.append(threading.Thread(target=read_logs, daemon=False))

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete and verify they finished
        hung_threads = []
        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                hung_threads.append(thread.name)

        # Fail fast if any threads are still running
        assert len(hung_threads) == 0, f"Threads did not complete within timeout: {hung_threads}"

        # Check that no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Check that all operations completed successfully
        assert len(results) == 6  # 3 write + 3 read operations
        assert all("success" in result for result in results)