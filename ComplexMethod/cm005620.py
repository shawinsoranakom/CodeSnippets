def __next__(self):
        if self._loader_batch_index is not None and self._loader_batch_index < self.loader_batch_size:
            # We are currently unrolling a batch so we just need to return
            # the current item within a batch
            return self.loader_batch_item()

        # We're out of items within a batch
        item = next(self.iterator)
        processed = self.infer(item, **self.params)
        # We now have a batch of "inferred things".
        if self.loader_batch_size is not None:
            # Try to infer the size of the batch
            if isinstance(processed, torch.Tensor):
                first_tensor = processed
            elif isinstance(processed, tuple):
                first_tensor = processed[0]
            else:
                key = list(processed.keys())[0]
                first_tensor = processed[key]

            if isinstance(first_tensor, list):
                observed_batch_size = len(first_tensor)
            else:
                observed_batch_size = first_tensor.shape[0]
            if 0 < observed_batch_size < self.loader_batch_size:
                # could be last batch so we can't unroll as many
                # elements.
                self.loader_batch_size = observed_batch_size
            # Setting internal index to unwrap the batch
            self._loader_batch_data = processed[0] if isinstance(processed, tuple) else processed
            self._loader_batch_index = 0
            return self.loader_batch_item()
        else:
            # We're not unrolling batches
            return processed