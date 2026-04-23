def free_buf(
        self,
        is_free_fn: Callable[[int, memoryview], bool],
        nbytes: int | None = None,
    ) -> Iterable[int]:
        """
        Free a buffer of the given size. This is a no-op in shared memory,
        but we need to keep track of the metadata.

        If freed memory spreads across the end and start of the ring buffer,
        the actual freed memory will be in two segments. In this case there
        still might not be a contiguous space of `nbytes` available.

        Args:
            nbytes (int, optional): The size of the buffer to free. If None,
                frees the maximum size of the ring buffer.
        """

        assert self.is_writer, "Only the writer can free buffers."
        logger.debug(
            "Freeing up space in the ring buffer, "
            "monotonic_id_start: %d, monotonic_id_end: %d",
            self.monotonic_id_start,
            self.monotonic_id_end,
        )
        monotonic_id_before = self.monotonic_id_start
        # if nbytes is None, free up the maximum size of the ring buffer
        if nbytes is None:
            nbytes = self.data_buffer_size
        freed_bytes = 0
        while self.monotonic_id_start in self.metadata and freed_bytes < nbytes:
            address = self.metadata[self.monotonic_id_start]
            with self.access_buf(address) as (data_buff, metadata):
                if is_free_fn(self.monotonic_id_start, data_buff):
                    # check passed, we can free the buffer
                    del self.metadata[self.monotonic_id_start]
                    self.monotonic_id_start = (
                        self.monotonic_id_start + 1
                    ) % self.ID_MAX
                    if self.monotonic_id_start in self.metadata:
                        # pointing to the start addr of next allocation
                        self.data_buffer_start += (
                            self.metadata[self.monotonic_id_start]
                            - self.data_buffer_start
                        ) % self.data_buffer_size
                    else:
                        # no remaining allocation, reset to zero
                        self.data_buffer_start = self.data_buffer_end = 0
                    freed_bytes += metadata[1]
                else:
                    # there are still readers, we cannot free the buffer
                    break

        logger.debug(
            "Freed %d bytes from the ring buffer, "
            "monotonic_id_start: %d, monotonic_id_end: %d",
            freed_bytes,
            self.monotonic_id_start,
            self.monotonic_id_end,
        )

        # buffer wrap around
        if self.data_buffer_start >= self.data_buffer_size:
            self.data_buffer_start -= self.data_buffer_size
            self.data_buffer_end -= self.data_buffer_size

        monotonic_id_after = self.monotonic_id_start
        # id wrap around
        if monotonic_id_after >= monotonic_id_before:
            return range(monotonic_id_before, monotonic_id_after)
        else:
            return chain(
                range(monotonic_id_before, self.ID_MAX), range(0, monotonic_id_after)
            )