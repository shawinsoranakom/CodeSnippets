def __next__(self):
        # Extremely similar to PipelineIterator in its unpacking mechanism
        # BUT, we have an extra required item which is the presence of `is_last`
        # That is because everything is flattened by `PipelineChunkIterator` we
        # need to keep track of how to regroup here in the original `process`
        # boundaries so that `process` and `postprocess` see the same data.

        # This iterator accumulates items (possibly while unbatching) until it
        # its a `is_last` and then just passes it on to the caller.
        is_last = False
        accumulator = []
        if self._loader_batch_index is not None and self._loader_batch_index < self.loader_batch_size:
            while self._loader_batch_index < self.loader_batch_size:
                item = self.loader_batch_item()
                is_last = item.pop("is_last")
                accumulator.append(item)
                if is_last:
                    return accumulator

        while not is_last:
            processed = self.infer(next(self.iterator), **self.params)
            if self.loader_batch_size is not None:
                if isinstance(processed, torch.Tensor):
                    first_tensor = processed
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
                self._loader_batch_data = processed
                self._loader_batch_index = 0
                while self._loader_batch_index < self.loader_batch_size:
                    item = self.loader_batch_item()
                    is_last = item.pop("is_last")
                    accumulator.append(item)
                    if is_last:
                        return accumulator
            else:
                item = processed
                is_last = item.pop("is_last")
                accumulator.append(item)
        return accumulator