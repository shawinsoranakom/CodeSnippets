def _standardize_batch(self, batch):
        if isinstance(batch, dict):
            return batch
        if isinstance(batch, np.ndarray):
            batch = (batch,)
        if isinstance(batch, list):
            batch = tuple(batch)
        if not isinstance(batch, tuple) or len(batch) not in {1, 2, 3}:
            raise ValueError(
                "PyDataset.__getitem__() must return a tuple or a dict. "
                "If a tuple, it must be ordered either "
                "(input,) or (inputs, targets) or "
                "(inputs, targets, sample_weights). "
                f"Received: {str(batch)[:100]}... of type {type(batch)}"
            )
        if self.class_weight is not None:
            if len(batch) == 3:
                raise ValueError(
                    "You cannot specify `class_weight` "
                    "and `sample_weight` at the same time."
                )
            if len(batch) == 2:
                sw = data_adapter_utils.class_weight_to_sample_weights(
                    batch[1], self.class_weight
                )
                batch = batch + (sw,)
        return batch