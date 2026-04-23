def compute_output_spec(self, x):
        x_shape = x.shape

        if len(x_shape) == 0:
            flat_size = 1
        elif len(x_shape) == 1:
            flat_size = x_shape[0] if x_shape[0] is not None else None
        else:
            flat_size = None
            for s in x_shape:
                if s is None:
                    flat_size = None
                    break
                elif flat_size is None:
                    flat_size = s
                else:
                    flat_size *= s

        if flat_size is None:
            output_shape = [None, None]
        else:
            output_shape = [
                flat_size + int(np.abs(self.k)),
                flat_size + int(np.abs(self.k)),
            ]

        return KerasTensor(output_shape, dtype=x.dtype)