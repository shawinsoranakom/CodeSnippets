def loader_batch_item(self):
        """
        Return item located at `loader_batch_index` within the current `loader_batch_data`.
        """
        if isinstance(self._loader_batch_data, torch.Tensor):
            # Batch data is simple tensor, just fetch the slice
            result = self._loader_batch_data[self._loader_batch_index].unsqueeze(0)
        else:
            # Batch data is assumed to be BaseModelOutput (or dict)
            loader_batched = {}
            for k, element in self._loader_batch_data.items():
                if isinstance(element, ModelOutput):
                    # Convert ModelOutput to tuple first
                    element = element.to_tuple()
                    if isinstance(element[0], torch.Tensor):
                        loader_batched[k] = tuple(el[self._loader_batch_index].unsqueeze(0) for el in element)
                    elif isinstance(element[0], np.ndarray):
                        loader_batched[k] = tuple(np.expand_dims(el[self._loader_batch_index], 0) for el in element)
                    continue
                if k in {"hidden_states", "attentions"} and isinstance(element, tuple):
                    # Those are stored as lists of tensors so need specific unbatching.
                    if isinstance(element[0], torch.Tensor):
                        loader_batched[k] = tuple(el[self._loader_batch_index].unsqueeze(0) for el in element)
                    elif isinstance(element[0], np.ndarray):
                        loader_batched[k] = tuple(np.expand_dims(el[self._loader_batch_index], 0) for el in element)
                    continue
                if k == "past_key_values":
                    continue
                if element is None:
                    # This can happen for optional data that get passed around
                    loader_batched[k] = None
                elif isinstance(element[self._loader_batch_index], torch.Tensor):
                    # Take correct batch data, but make it looked like batch_size=1
                    # For compatibility with other methods within transformers

                    loader_batched[k] = element[self._loader_batch_index].unsqueeze(0)
                elif isinstance(element[self._loader_batch_index], np.ndarray):
                    # Take correct batch data, but make it looked like batch_size=1
                    # For compatibility with other methods within transformers
                    loader_batched[k] = np.expand_dims(element[self._loader_batch_index], 0)
                else:
                    # This is typically a list, so no need to `unsqueeze`.
                    loader_batched[k] = element[self._loader_batch_index]
            # Recreate the element by reusing the original class to make it look
            # batch_size=1
            result = self._loader_batch_data.__class__(loader_batched)
        self._loader_batch_index += 1
        return result