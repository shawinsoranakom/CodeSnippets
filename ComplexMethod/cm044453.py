def __getitem__(self, indices: slice) -> ExtractBatch:
        """Obtain a subset of this batch object with the data given by the start and end indices

        Parameters
        ----------
        indices
            The (start, stop, end) slice for extracting from the batch

        Returns
        -------
        A batch object containing the data from this object for the given indices
        """
        frame_ids = self.frame_ids[indices].copy()
        # If requesting the first bbox, we select all frames from the start
        frame_start = 0 if indices.start == 0 else frame_ids[0]

        frame_end = frame_ids[-1] + 1
        if indices.stop < self.bboxes.shape[0] and self.frame_ids[indices.stop] > frame_end:
            # catch any zero box frames between now and next split request
            frame_end = self.frame_ids[indices.stop]

        frame_sizes = None if self.frame_sizes is None else self.frame_sizes[frame_start:frame_end]
        frame_metadata = (None if self.frame_metadata is None
                          else self.frame_metadata[frame_start:frame_end])
        retval = ExtractBatch(self.filenames[frame_start:frame_end],
                              self.images[frame_start:frame_end],
                              sources=self.sources[frame_start:frame_end],
                              is_aligned=self.is_aligned,
                              frame_sizes=frame_sizes,
                              frame_metadata=frame_metadata,
                              passthrough=self.passthrough)
        retval.bboxes = self.bboxes[indices]
        retval.aligned = self.aligned[indices]
        retval.masks = {k: v[indices] for k, v in self.masks.items()}
        retval.identities = {k: v[indices] for k, v in self.identities.items()}

        if indices.start > 0:
            frame_ids -= frame_ids[0]  # Reset to zero
        retval.frame_ids = frame_ids

        if self.landmarks is not None:
            retval.landmarks = self.landmarks[indices]

        if hasattr(self, "data"):
            retval.data = self.data[indices]

        if hasattr(self, "matrices"):
            retval.matrices = self.matrices[indices]

        return retval