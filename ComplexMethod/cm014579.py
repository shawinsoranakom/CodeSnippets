def parse(args: str) -> Arguments:
        """
        Input: 'int x, int y, int z'
        """

        # We do this in two phases.  First we parse into three
        # main categories: positional, kwarg_only, out.
        # Then, we reparse positional and kwarg_only to separate
        # out the self argument and tensor options arguments.

        positional, kwarg_only, out = Arguments._preparse(args)

        # Split self argument
        self_ix = None
        for i, a in enumerate(positional):
            if a.name == "self":
                self_ix = i
                break
        pre_self_positional: list[Argument]
        self_arg: SelfArgument | None
        post_self_positional: list[Argument]
        if self_ix is not None:
            pre_self_positional = positional[:self_ix]
            self_arg = SelfArgument(positional[self_ix])
            post_self_positional = positional[self_ix + 1 :]
        else:
            pre_self_positional = []
            self_arg = None
            post_self_positional = positional

        # Group tensor options arguments
        pre_tensor_options_kwarg_only: list[Argument] = []
        tensor_options: TensorOptionsArguments | None = None
        post_tensor_options_kwarg_only: list[Argument] = []
        kwarg_only_acc = pre_tensor_options_kwarg_only

        def pred(name: str, ty: Type) -> Callable[[Argument], bool]:
            return lambda a: a.name == name and a.type in [ty, OptionalType(ty)]

        predicates = [  # order matters
            pred("dtype", Type.parse("ScalarType")),
            pred("layout", Type.parse("Layout")),
            pred("device", Type.parse("Device")),
            pred("pin_memory", Type.parse("bool")),
        ]

        i = 0
        while i < len(kwarg_only):
            # If there is enough space...
            if i <= len(kwarg_only) - len(predicates):
                # And the next len(predicates) arguments look like TensorOptions arguments
                if all(
                    p(a)
                    for p, a in zip(predicates, kwarg_only[i : i + len(predicates)])
                ):
                    if kwarg_only_acc is not pre_tensor_options_kwarg_only:
                        raise AssertionError(
                            "tensor options arguments can only appear once"
                        )
                    # Group them together as one argument
                    tensor_options = TensorOptionsArguments(
                        dtype=kwarg_only[i],
                        layout=kwarg_only[i + 1],
                        device=kwarg_only[i + 2],
                        pin_memory=kwarg_only[i + 3],
                    )
                    i += len(predicates)
                    kwarg_only_acc = post_tensor_options_kwarg_only
                    continue
            kwarg_only_acc.append(kwarg_only[i])
            i += 1

        return Arguments(
            pre_self_positional=tuple(pre_self_positional),
            self_arg=self_arg,
            post_self_positional=tuple(post_self_positional),
            pre_tensor_options_kwarg_only=tuple(pre_tensor_options_kwarg_only),
            tensor_options=tensor_options,
            post_tensor_options_kwarg_only=tuple(post_tensor_options_kwarg_only),
            out=tuple(out),
        )