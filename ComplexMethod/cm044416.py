def _process(self) -> None:  # noqa[C901]
        """ Process the output from the extraction pipeline within a thread """
        logger.debug("[Extract.Output] start")
        total_batches = len(self._batches)
        self._set_saver(self._outputs[0])
        if self._saver is not None and self._min_size > 0:
            logger.info("Only outputting faces that have been resized from a minimum resolution "
                        "of %spx", self._min_size)

        for batch_idx, batch in enumerate(self._batches):
            msg = f" job {batch_idx + 1} of {total_batches}" if total_batches > 1 else ""
            logger.info("Processing%s: '%s'", msg, batch.loader.location)
            if self._saver is not None:
                logger.info("Faces output: '%s'", self._saver.location)
            has_started = False
            save_interval = 0 if not batch.alignments.save_alignments else self._save_interval
            with tqdm(desc="Extracting faces",
                      total=batch.loader.count,
                      leave=True,
                      smoothing=0) as prog_bar:
                if batch_idx > 0:  # Update for batch picked up at end of previous batch
                    prog_bar.update(1)

                for idx, media in enumerate(self._pipeline):
                    if not has_started:
                        prog_bar.reset()  # Delay before first output, reset timer for better it/s
                        has_started = True

                    if media.source != batch.loader.location:
                        self._finalize_batch(batch, batch_idx)
                        next_batch = self._batches[batch_idx + 1]
                        self._process_faces(media, next_batch.alignments,
                                            next_batch.loader.is_video)
                        break

                    self._process_faces(media, batch.alignments, batch.loader.is_video)
                    if save_interval and (idx + 1) % save_interval == 0:
                        batch.alignments.save()
                    if prog_bar.n + 1 > prog_bar.total:
                        # Don't switch to unknown mode when frame count is under
                        prog_bar.total += 1
                    prog_bar.update(1)

        if self._thread.error_state.has_error:
            logger.debug("[Extract.Output] Thread error detected in worker thread")
            return
        self._finalize_batch(self._batches[-1], len(self._batches) - 1)
        logger.debug("[Extract.Output] end")