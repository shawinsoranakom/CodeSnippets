def _standardize_shapes(path, tensor, shape):  # type: ignore[no-untyped-def]
        """
        Helps standardize the dynamic_shapes tree structure we serialize,
        returning lists for each tensor shape, handling tensor-level Nones.
        """
        if not isinstance(tensor, torch.Tensor):
            return None
        if shape is None:
            return [Dim.STATIC] * len(tensor.shape)

        out = []
        if isinstance(shape, dict):
            for i, s in enumerate(tensor.shape):
                out.append(s if shape.get(i) is None else shape.get(i))
        else:
            if not isinstance(shape, (tuple, list)):
                raise AssertionError(f"expected tuple or list, got {type(shape)}")
            for i, s in enumerate(tensor.shape):
                out.append(s if shape[i] is None else shape[i])
        return out