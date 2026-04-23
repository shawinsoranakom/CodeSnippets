def compute_output_spec(self, x):
        x_shape = list(x.shape)
        output_shape = [-1 for _ in range(len(x.shape))]
        for sc, dst in zip(self.source, self.destination):
            output_shape[dst] = x_shape[sc]
            x_shape[sc] = -1
        i, j = 0, 0
        while i < len(output_shape):
            while i < len(output_shape) and output_shape[i] != -1:
                # Find the first dim unset.
                i += 1
            while j < len(output_shape) and x_shape[j] == -1:
                # Find the first dim not being passed.
                j += 1
            if i == len(output_shape):
                break
            output_shape[i] = x_shape[j]
            i += 1
            j += 1
        return KerasTensor(output_shape, dtype=x.dtype)