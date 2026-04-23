def __torch_function__(
        self,
        func: OpOverload,
        types: Sequence[type],
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
    ) -> FakeTensor:
        kwargs = kwargs if kwargs else {}

        # clone will get called in Parameter deepcopy
        if func is torch._C.TensorBase.clone:
            if not isinstance(args[0], Tensor):
                raise AssertionError(f"Expected Tensor, got {type(args[0])}")
            return func(
                self.fake_mode.from_tensor(args[0], static_shapes=True), **kwargs
            )
        elif func is Tensor.__deepcopy__:
            if len(args) != 2 or len(kwargs) != 0:
                raise AssertionError(
                    f"Expected 2 args and 0 kwargs for __deepcopy__, got {len(args)} args and {len(kwargs)} kwargs"
                )
            tensor = cast(Tensor, args[0])
            memo = cast(dict[int, FakeTensor], args[1])

            if id(tensor) in memo:
                return memo[id(tensor)]

            out = self.fake_mode.from_tensor(tensor, static_shapes=True)
            memo[id(tensor)] = out
            return out
        else:
            with torch._C.DisableTorchFunctionSubclass():
                return func(*args, **kwargs)