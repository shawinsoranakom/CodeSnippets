def _handle_load_task(self, task) -> None:
        """Handle individual load task."""
        request_id, block_ids, block_hashes, future = task
        start_time = time.perf_counter()
        buffers = None
        try:
            # Step1: Get block locations from metadata server
            page_indices = self._connector._metadata_client.get_key_locations(
                self._rank, block_hashes
            )

            if any(idx is None for idx in page_indices):
                return self._fail_task("Loaded", "Blocks not found", request_id, future)

            # Allocate read buffer
            buffers = self._load_buffer_allocator.alloc_buffer(len(block_ids))
            if buffers is None:
                return self._fail_task(
                    "Loaded",
                    f"Buffer allocation failed for {len(block_ids)} blocks",
                    request_id,
                    future,
                )

            # Step2: Read data in batches
            offsets = [idx * self._bytes_per_page for idx in page_indices]
            read_futures = []
            for i in range(0, len(offsets), DEFAULT_MAX_IO_ENTRIES):
                batch_offsets = offsets[i : i + DEFAULT_MAX_IO_ENTRIES]
                batch_buffers = buffers[i : i + DEFAULT_MAX_IO_ENTRIES]
                client = self._connector._clients[self._connector._ac.next()]
                read_future = self._io_executor.submit(
                    client.batch_read, batch_offsets, batch_buffers
                )
                read_futures.append(read_future)

            # Check read results
            read_success = all(
                result == self._bytes_per_page
                for read_future in read_futures
                for result in read_future.result()
            )

            if not read_success:
                self._load_buffer_allocator.free_buffer(buffers)
                return self._fail_task(
                    "Loaded", "Read operation failed", request_id, future
                )

            # Step3: Scatter data back to KV cache
            with torch.cuda.stream(self._load_stream):
                self._connector._gather_or_scatter_kv_caches(
                    block_ids, buffers, "scatter"
                )

            self._load_stream.synchronize()
            self._load_buffer_allocator.free_buffer(buffers)
            return self._succeed_task(
                "Loaded", start_time, request_id, len(block_ids), future
            )

        except Exception as e:
            if buffers is not None:
                self._load_buffer_allocator.free_buffer(buffers)
            return self._fail_task(
                "Loaded", f"Task execution error: {e}", request_id, future
            )