def resize(self, *new_shape, refcheck=False):
        # NB: differs from np.resize: fills with zeros instead of making repeated copies of input.
        if refcheck:
            raise NotImplementedError(
                f"resize(..., refcheck={refcheck} is not implemented."
            )
        if new_shape in [(), (None,)]:
            return

        # support both x.resize((2, 2)) and x.resize(2, 2)
        if len(new_shape) == 1:
            new_shape = new_shape[0]
        if isinstance(new_shape, int):
            new_shape = (new_shape,)

        if builtins.any(x < 0 for x in new_shape):
            raise ValueError("all elements of `new_shape` must be non-negative")

        new_numel, old_numel = math.prod(new_shape), self.tensor.numel()

        self.tensor.resize_(new_shape)

        if new_numel >= old_numel:
            # zero-fill new elements
            if not self.tensor.is_contiguous():
                raise AssertionError("tensor must be contiguous for resize with growth")
            b = self.tensor.flatten()  # does not copy
            b[old_numel:].zero_()