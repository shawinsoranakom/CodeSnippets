def append(self, batch: ExtractBatchAligned) -> None:
        """Append the data from the given batch object to this batch object

        Parameters
        ----------
        batch
            The object containing data to be appended to this object
        """
        if batch.landmarks is not None:
            self.landmarks = (np.concatenate([self.landmarks, batch.landmarks])
                              if self.landmarks is not None else batch.landmarks)
            if self.landmark_type is None:
                self.landmark_type = batch.landmark_type

        for k, v in batch.__dict__.items():
            if k.startswith("_cache_") and v is not None:
                exist = getattr(self, k)
                val = None if exist is None else np.concatenate([exist, v])
                setattr(self, k, val)