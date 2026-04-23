def append(self, batch: FrameFaces) -> None:
        """Append the data from the given batch object to this batch object

        Parameters
        ----------
        batch
            The object containing data to be appended to this object
        """
        assert batch.filename == self.filename
        assert batch.source == self.source
        assert batch.passthrough == self.passthrough
        assert batch.frame_metadata == self.frame_metadata

        if not np.any(self.image):  # Image potentially deleted from previous split batch
            self.image = batch.image
        self.bboxes = np.concatenate([self.bboxes, batch.bboxes])
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