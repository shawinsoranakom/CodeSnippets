def __next__(self) -> FrameFaces:
        """ Get the next batch of data from the iterator

        Returns
        -------
        A FrameFaces object for a single frame

        Raises
        ------
        StopIteration
            When the input is exhausted
        """
        self._handle_signals()
        while True:
            self._check_error()
            retval = self._from_fifo()
            if retval is not None:
                return retval

            batch: ExtractBatch | ExtractSignal | FrameFaces | None = self._from_queue()
            if batch is None:
                continue

            if isinstance(batch, ExtractSignal):
                batch = self._handle_inbound_signal(batch)
            if isinstance(batch, FrameFaces):
                return batch
            if batch == ExtractSignal.FLUSH:
                continue  # Don't flush to output. Wait for next batch

            assert isinstance(batch, ExtractBatch)
            if batch.passthrough:
                return self._handle_passthrough_batch(batch)

            self._to_extract_media(batch)