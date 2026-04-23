def _put_data(self, process: str, batch: ExtractBatch | ExtractSignal) -> None:
        """Put data from a plugin's process into the next queue. If this is the first plugin in
        the pipeline and we are queueing data out from the plugin, then remove any images which
        have no detected faces.

        Parameters
        ----------
        process
            The name of the process that wishes to output data
        batch
            The batch of data to put to the next queue or an ExtractSignal after the final
            iteration
        """
        queue_names = list(self._queues)
        queue_index = queue_names.index(process) + 1
        next_process = T.cast(T.Literal["process", "post_process", "out"],
                              queue_names[queue_index])
        assert next_process in ("process", "post_process", "out")
        queue = self._queues[next_process]
        self._clean_output(batch, next_process)
        logger.trace("[%s.%s] Outputting to '%s': %s",  # type:ignore[attr-defined]
                     self._plugin_name,
                     process,
                     next_process,
                     batch.name if isinstance(batch, ExtractSignal) else batch)

        while True:
            if self._threads.error_state.has_error:
                logger.debug("[%s.%s] thread error detected. Not putting",
                             self._plugin_name, process)
                return
            try:
                logger.trace("[%s.%s] Putting to out queue: %s",  # type:ignore[attr-defined]
                             self._plugin_name,
                             process,
                             batch.name if isinstance(batch, ExtractSignal) else batch)
                queue.put(batch, timeout=0.2)
                break
            except QueueFull:
                logger.trace("[%s.%s] Waiting to put item",  # type:ignore[attr-defined]
                             self._plugin_name, process)
                continue

        if next_process == "out" and isinstance(batch, ExtractSignal):
            sleep(1)  # Wait for downstream plugins to flush
            self.handler.output_info()