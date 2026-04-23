def append(self, batch: ExtractBatch) -> None:  # noqa[C901]
        """Append the data from the given batch object to this batch object

        Parameters
        ----------
        batch
            The object containing data to be appended to this object
        """
        if not self.filenames:
            self._populate_batch(batch)
            return
        frame_offset = len(self.filenames)
        if self.filenames[-1] == batch.filenames[0]:
            frame_offset -= 1  # We are still on the same frame
            if not np.any(self.images[-1]) and np.any(batch.images[0]):
                # Image was stripped for the faces in this batch, but exist for incoming batch
                self.images[-1] = batch.images[0]
        batch.frame_ids += frame_offset

        existing_filenames = self.filenames[:]
        self.filenames.extend(f for f in batch.filenames if f not in existing_filenames)
        self.images.extend(batch.images[i] for i, f in enumerate(batch.filenames)
                           if f not in existing_filenames)
        self.sources.extend(batch.sources[i] for i, f in enumerate(batch.filenames)
                            if f not in existing_filenames)

        if self.frame_sizes is not None and batch.frame_sizes is not None:
            self.frame_sizes.extend(batch.frame_sizes[i] for i, f in enumerate(batch.filenames)
                                    if f not in existing_filenames)
        if self.frame_metadata is not None and batch.frame_metadata is not None:
            self.frame_metadata.extend(batch.frame_metadata[i]
                                       for i, f in enumerate(batch.filenames)
                                       if f not in existing_filenames)

        self.bboxes = np.concatenate([self.bboxes, batch.bboxes])
        self.frame_ids = np.concatenate([self.frame_ids, batch.frame_ids])
        self.aligned.append(batch.aligned)

        for name, masks in batch.masks.items():
            if name in self.masks:
                self.masks[name].append(masks)
            else:
                self.masks[name] = masks

        for name, identities in batch.identities.items():
            self.identities[name] = (np.concatenate([self.identities[name], identities])
                                     if name in self.identities
                                     else identities)

        if hasattr(self, "data"):
            self.data = np.concatenate([self.data, batch.data])

        if hasattr(self, "matrices"):
            self.matrices = np.concatenate([self.matrices, batch.matrices])