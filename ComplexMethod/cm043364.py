def _extract_with_chunking(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract tables using chunking and parallel processing.
        """
        if self.verbose:
            self._log("info", f"Starting chunked extraction for content with {len(html_content)} characters")

        # Create smart chunks
        chunks, has_headers = self._create_smart_chunks(html_content)

        if self.verbose:
            self._log("info", f"Created {len(chunks)} chunk(s) for processing")

        if len(chunks) == 1:
            # No need for parallel processing
            if self.verbose:
                self._log("info", "Processing as single chunk (no parallelization needed)")
            result = self._process_chunk(chunks[0], 0, 1, has_headers)
            return [result['table']] if result.get('table') else []

        # Process chunks in parallel
        if self.verbose:
            self._log("info", f"Processing {len(chunks)} chunks in parallel (max workers: {self.max_parallel_chunks})")

        chunk_results = []
        with ThreadPoolExecutor(max_workers=self.max_parallel_chunks) as executor:
            # Submit all chunks for processing
            futures = {
                executor.submit(self._process_chunk, chunk, i, len(chunks), has_headers): i
                for i, chunk in enumerate(chunks)
            }

            # Collect results as they complete
            for future in as_completed(futures):
                chunk_index = futures[future]
                try:
                    result = future.result(timeout=60)  # 60 second timeout per chunk
                    if self.verbose:
                        self._log("info", f"Chunk {chunk_index + 1}/{len(chunks)} completed successfully")
                    chunk_results.append(result)
                except Exception as e:
                    if self.verbose:
                        self._log("error", f"Chunk {chunk_index + 1}/{len(chunks)} processing failed: {str(e)}")
                    chunk_results.append({'chunk_index': chunk_index, 'table': None, 'error': str(e)})

        if self.verbose:
            self._log("info", f"All chunks processed, merging results...")

        # Merge results
        return self._merge_chunk_results(chunk_results)