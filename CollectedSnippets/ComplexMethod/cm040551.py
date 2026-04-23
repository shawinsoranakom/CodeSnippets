def compute_output_spec(self, x, key):
        remaining_shape = list(x.shape)
        new_shape = []
        if isinstance(key, int):
            remaining_key = [key]
        elif isinstance(key, tuple):
            remaining_key = list(key)
        elif isinstance(key, list):
            remaining_key = key.copy()
        else:
            raise ValueError(
                f"Unsupported key type for array slice. Received: `{key}`"
            )
        num_ellipses = remaining_key.count(Ellipsis)
        if num_ellipses > 1:
            raise ValueError(
                f"Slice should only have one ellipsis. Received: `{key}`"
            )
        elif num_ellipses == 0:
            # Add an implicit final ellipsis.
            remaining_key.append(Ellipsis)
        # Consume slice key element by element.
        while True:
            if not remaining_key:
                break
            subkey = remaining_key.pop(0)
            # Check for `newaxis` and `Ellipsis`.
            if subkey == Ellipsis:
                # Keep as many slices remain in our key, omitting `newaxis`.
                needed = len(remaining_key) - remaining_key.count(np.newaxis)
                consumed = len(remaining_shape) - needed
                new_shape += remaining_shape[:consumed]
                remaining_shape = remaining_shape[consumed:]
                continue
            # All frameworks follow numpy for newaxis. `np.newaxis == None`.
            if subkey == np.newaxis:
                new_shape.append(1)
                continue
            # At this point, we need to consume a new axis from the shape.
            if not remaining_shape:
                raise ValueError(
                    f"Array has shape {x.shape} but slice "
                    f"has to many indices. Received: `{key}`"
                )
            length = remaining_shape.pop(0)
            if isinstance(subkey, int):
                if length is not None:
                    index = subkey if subkey >= 0 else subkey + length
                    if index < 0 or index >= length:
                        raise ValueError(
                            f"Array has shape {x.shape} but out-of-bounds "
                            f"index {key} was requested."
                        )
            elif isinstance(subkey, slice):
                if length is not None:
                    # python3 friendly way to compute a slice length.
                    new_length = len(range(*subkey.indices(length)))
                    new_shape.append(new_length)
                else:
                    new_shape.append(length)
            else:
                raise ValueError(
                    f"Unsupported key type for array slice. Received: `{key}`"
                )
        return KerasTensor(tuple(new_shape), dtype=x.dtype)