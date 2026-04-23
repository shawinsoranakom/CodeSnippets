def _validate_noise_shape(self, noise_shape):
        if noise_shape is None:
            return None

        if isinstance(noise_shape, str):
            raise ValueError(
                f"Invalid value received for argument `noise_shape`. "
                f"Expected a tuple or list of integers. "
                f"Received: noise_shape={noise_shape}"
            )

        if not isinstance(noise_shape, tuple):
            try:
                noise_shape = tuple(noise_shape)
            except TypeError:
                raise ValueError(
                    f"Invalid value received for argument `noise_shape`. "
                    f"Expected an iterable of integers "
                    f"(e.g., a tuple or list). "
                    f"Received: noise_shape={noise_shape}"
                )

        for i, dim in enumerate(noise_shape):
            if dim is not None:
                if not isinstance(dim, int):
                    raise ValueError(
                        f"Invalid value received for argument `noise_shape`. "
                        f"Expected all elements to be integers or None. "
                        f"Received element at index {i}: {dim} "
                        f"(type: {type(dim).__name__})"
                    )

                if dim <= 0:
                    raise ValueError(
                        f"Invalid value received for argument `noise_shape`. "
                        f"Expected all dimensions to be positive integers "
                        f"or None. "
                        f"Received negative or zero value at index {i}: {dim}"
                    )

        return noise_shape