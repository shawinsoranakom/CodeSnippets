def __call__(self, fn):
        if self.compile:
            kwargs = {}
            if self.backend is not None:
                kwargs["backend"] = self.backend
            if self.mode is not None:
                kwargs["mode"] = self.mode
            if self.options is not None:
                options = {
                    k: v
                    for k, v in self.options.items()
                    if k in torch._inductor.list_options()
                }
                kwargs["options"] = options
            return torch.compile(fn, **kwargs)
        assert self.backend is None  # noqa: S101
        assert self.mode is None  # noqa: S101
        assert self.options is None  # noqa: S101
        return fn