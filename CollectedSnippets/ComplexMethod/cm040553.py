def compute_output_spec(self, indices):
        if None in self.shape:
            output_shapes = [[None] for _ in self.shape]
        else:
            if isinstance(indices, int):
                output_shapes = [[1] for _ in self.shape]
            elif hasattr(indices, "shape"):
                output_shapes = [list(indices.shape) for _ in self.shape]
            else:
                try:
                    indices_shape = np.shape(indices)
                    output_shapes = [list(indices_shape) for _ in self.shape]
                except Exception:
                    output_shapes = [[None] for _ in self.shape]

        return [
            KerasTensor(shape, dtype=indices.dtype) for shape in output_shapes
        ]