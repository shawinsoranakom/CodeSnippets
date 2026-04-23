def __call__(self, inputs, scalars=None, **kwargs):
        if scalars is not None:
            if len(inputs) != 3:
                raise AssertionError(f"expected len(inputs) == 3, got {len(inputs)}")
            # We need to distribute each scalar to the regular func and it needs
            # special consideration as it is a keyword only argument to the
            # regular func. (Strangely, it is not a keyword only argument to the
            # foreach func)
            return [
                self.func(*i, value=scalars[idx], **kwargs)
                for idx, i in enumerate(zip(*inputs))
            ]
        if len(inputs) == 2 and isinstance(inputs[1], (Number, torch.Tensor)):
            # binary op with tensorlist and scalar.
            inputs[1] = [inputs[1] for _ in range(len(inputs[0]))]
        return [self.func(*i, **kwargs) for i in zip(*inputs)]