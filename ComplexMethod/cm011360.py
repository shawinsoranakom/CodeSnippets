def read_data(self, plan: LoadPlan, planner: LoadPlanner) -> Future[None]:
        from safetensors import safe_open  # type: ignore[import]

        per_file: dict[str, list[ReadItem]] = {}

        for read_item in plan.items:
            item_md: _HFStorageInfo = self.storage_data[read_item.storage_index]
            file_name = item_md.relative_path
            per_file.setdefault(file_name, []).append(read_item)

        if self.thread_count <= 1 or len(per_file) <= 1:
            for file_name, reqs in per_file.items():
                with safe_open(filename=file_name, framework="pt") as f:
                    for req in reqs:
                        self._process_read_request(f, req, planner)
        else:
            # Use parallel implementation with thread pool
            file_queue: queue.Queue = queue.Queue()
            result_queue: queue.Queue = queue.Queue()

            # Fill the queue with files to process
            for file_name, reqs in per_file.items():
                file_queue.put((file_name, reqs))

            # Create and start worker threads
            threads = []
            num_threads = min(self.thread_count, len(per_file))
            for _ in range(num_threads):
                t = threading.Thread(
                    target=self._read_files_from_queue,
                    args=(file_queue, result_queue, planner),
                )
                t.start()
                threads.append(t)

            # Wait for all threads to complete
            for t in threads:
                t.join()

            # Check if all files were processed
            processed_count = 0
            try:
                while True:
                    result_queue.get_nowait()
                    processed_count += 1
            except queue.Empty:
                pass

            if processed_count != len(per_file):
                raise AssertionError(
                    f"Not all files were processed: {processed_count} out of {len(per_file)}"
                )

        fut: Future = Future()
        fut.set_result(None)
        return fut