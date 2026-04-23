def _to_extract_media(self, batch: ExtractBatch) -> None:
        """ Process the incoming batch data into FrameFaces objects and return the next stored in
        local cache for output

        Parameters
        ----------
        batch
            The output ExtractBatch object from a plugin
        """
        merge = self._fifo and batch.filenames[0] == self._fifo[-1].filename
        lengths = batch.lengths
        starts = np.cumsum(lengths, dtype=np.int32) - lengths
        for idx, (filename, image, source, start, length) in enumerate(zip(batch.filenames,
                                                                           batch.images,
                                                                           batch.sources,
                                                                           starts,
                                                                           lengths)):

            end = start + length
            media = FrameFaces(
                filename,
                image,
                bboxes=batch.bboxes[start:end],
                identities={k: v[start:end] for k, v in batch.identities.items()},
                masks={k: v[start:end] for k, v in batch.masks.items()},
                source=source,
                is_aligned=batch.is_aligned,
                frame_metadata=None if batch.frame_metadata is None else batch.frame_metadata[idx],
                passthrough=batch.passthrough)
            media.aligned = batch.aligned[start:end]

            if merge and idx == 0:
                logger.trace(  # type:ignore[attr-defined]
                    "[%s] Merging %s faces to last batch: '%s'", self._name, len(media), filename)
                self._fifo[-1].append(media)
            else:
                self._fifo.append(media)

            logger.trace(  # type:ignore[attr-defined]
                "[%s] Split to FrameFaces: '%s' (%s faces)",
                self._name,
                self._fifo[-1].filename,
                len(self._fifo[-1]))