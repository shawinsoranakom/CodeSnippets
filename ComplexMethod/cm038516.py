def _handle_save_task(self, task) -> None:
        """Handle individual save task with proper stream synchronization."""
        request_id, block_ids, block_hashes, future, main_stream_event = task
        start_time = time.perf_counter()
        buffers = None
        try:
            # Step1: Allocate storage pages
            key_pairs = [(hash_val, "") for hash_val in block_hashes]
            allocation_results = (
                self._connector._metadata_client.allocate_pages_for_keys(
                    self._rank, key_pairs
                )
            )

            if any(result[1] < 0 for result in allocation_results):
                return self._fail_task(
                    "Saved", "Page allocation failed", request_id, future
                )

            page_indices = [result[1] for result in allocation_results]
            offsets = [idx * self._bytes_per_page for idx in page_indices]

            # Step2: Allocate buffers and gather KV cache data
            buffers = self._save_buffer_allocator.alloc_buffer(len(block_ids))
            if buffers is None:
                return self._fail_task(
                    "Saved",
                    f"Buffer allocation failed for {len(block_ids)} blocks",
                    request_id,
                    future,
                )

            # Synchronize streams and gather data
            with torch.cuda.stream(self._save_stream):
                self._save_stream.wait_event(main_stream_event)  # Wait for main stream
                self._connector._gather_or_scatter_kv_caches(
                    block_ids, buffers, "gather"
                )

                save_stream_event = torch.cuda.Event()
                save_stream_event.record(self._save_stream)  # Record gather completion

            # Step3: Write data in batches
            write_futures = []
            for i in range(0, len(offsets), DEFAULT_MAX_IO_ENTRIES):
                batch_offsets = offsets[i : i + DEFAULT_MAX_IO_ENTRIES]
                batch_buffers = buffers[i : i + DEFAULT_MAX_IO_ENTRIES]
                client = self._connector._clients[self._connector._ac.next()]
                write_future = self._io_executor.submit(
                    client.batch_write, batch_offsets, batch_buffers, save_stream_event
                )
                write_futures.append(write_future)

            # Check write results
            write_success = all(
                result == self._bytes_per_page
                for write_future in write_futures
                for result in write_future.result()
            )

            # Step4: Confirm writes to metadata server
            if write_success:
                written_keys = list(zip(block_hashes, page_indices))
                self._connector._metadata_client.confirm_write_for_keys(
                    self._rank, written_keys, []
                )
                self._save_buffer_allocator.free_buffer(buffers)
                return self._succeed_task(
                    "Saved", start_time, request_id, len(block_ids), future
                )
            else:
                self._connector._metadata_client.confirm_write_for_keys(
                    self._rank, [], page_indices
                )
                self._save_buffer_allocator.free_buffer(buffers)
                return self._fail_task(
                    "Saved", "Write operation failed", request_id, future
                )

        except Exception as e:
            if buffers is not None:
                self._save_buffer_allocator.free_buffer(buffers)
            return self._fail_task(
                "Saved", f"Task execution error: {e}", request_id, future
            )