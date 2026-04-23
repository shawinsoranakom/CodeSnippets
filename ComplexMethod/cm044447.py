def __next__(self) -> ExtractBatch | ExtractSignal:
        """ Get the next batch of data from the iterator. Depending on the plugin type calling this
        iterator, a batch object will be returned for the given batch size of frames (for detect
        plugins) or faces (for all other plugins)

        Returns
        -------
        ExtractBatch or ExtractSignal
            A new ExtractBatch object containing the batch to process through the plugin or an
            ExtractSignal

        Raises
        ------
        StopIteration
            When the input is exhausted
        """
        flush = self._handle_signals()
        if flush:
            return flush

        while True:
            self._check_error()
            retval = self._from_fifo()  # In loop as re-batching may need to run multiple times
            if retval is not None:
                return retval

            batch = self._from_queue()
            if batch is None:
                continue

            if isinstance(batch, ExtractBatch) and batch.passthrough and self._fifo:
                raise RuntimeError("Pipeline must be empty when adding a passthrough object")

            if isinstance(batch, ExtractBatch) and batch.passthrough:
                return batch

            if isinstance(batch, ExtractBatch):
                self._rebatch_data(batch)
                continue

            return self._handle_inbound_signal(batch)