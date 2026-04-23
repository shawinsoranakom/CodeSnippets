def _adjust_input_rank(self, flat_inputs):
        adjusted = []
        for i, x in enumerate(flat_inputs):
            ref_shape = self._inputs[i].shape
            if x is None:
                adjusted.append(x)
                continue
            x_rank = len(x.shape)
            ref_rank = len(ref_shape)
            if x_rank == ref_rank:
                adjusted.append(x)
                continue
            if x_rank == ref_rank + 1:
                if x.shape[-1] == 1:
                    adjusted.append(ops.squeeze(x, axis=-1))
                    continue
            if x_rank == ref_rank - 1:
                if ref_shape[-1] == 1:
                    adjusted.append(ops.expand_dims(x, axis=-1))
                    continue
            flat_paths_and_inputs = tree.flatten_with_path(self._inputs_struct)
            path = ".".join(str(p) for p in flat_paths_and_inputs[i][0])
            raise ValueError(
                f"Invalid input shape for input {x} with name "
                f"'{self._inputs[i].name}' and path '{path}'. Expected shape "
                f"{ref_shape}, but input has incompatible shape {x.shape}"
            )
        # Add back metadata.
        for i in range(len(flat_inputs)):
            if hasattr(flat_inputs[i], "_keras_history"):
                adjusted[i]._keras_history = flat_inputs[i]._keras_history
            mask = backend.get_keras_mask(flat_inputs[i])
            if mask is not None:
                backend.set_keras_mask(adjusted[i], mask)
        return adjusted