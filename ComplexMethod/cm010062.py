def impl(
        self, op_name, fn, dispatch_key="", *, with_keyset=False, allow_override=False
    ):
        r"""Registers the function implementation for an operator defined in the library.

        Args:
            op_name: operator name (along with the overload) or OpOverload object.
            fn: function that's the operator implementation for the input dispatch key or :func:`~fallthrough_kernel`
                to register a fallthrough.
            dispatch_key: dispatch key that the input function should be registered for. By default, it uses
                          the dispatch key that the library was created with.
            with_keyset: flag controlling if the current dispatcher call keyset should be passed as the first argument
                         to :attr:`fn` when calling. This should be used to create the appropriate keyset for redispatch calls.
            allow_override: Flag controlling if we want to override an
                         existing registered kernel implementation. This is by
                         default off, and will error you're trying to register a
                         kernel to a dispatch key with a kernel already
                         registered.

        Example::
            >>> # xdoctest: +SKIP("Requires Python <= 3.11")
            >>> my_lib = Library("aten", "IMPL")
            >>> def div_cpu(self, other):
            >>>     return self * (1 / other)
            >>> my_lib.impl("div.Tensor", div_cpu, "CPU")
        """

        if not callable(fn):
            raise TypeError(
                f"Input function is required to be a callable but found type {type(fn)}"
            )
        if dispatch_key == "":
            dispatch_key = self.dispatch_key

        if isinstance(op_name, str):
            name = op_name
        elif isinstance(op_name, OpOverload):
            name = op_name._schema.name
            overload_name = op_name._schema.overload_name
            if overload_name != "":
                name = name + "." + overload_name
        else:
            raise RuntimeError(
                "impl should be passed either a name or an OpOverload object as the first argument"
            )

        key = self.ns + "/" + name.split("::")[-1] + "/" + dispatch_key
        if (not allow_override) and key in _impls:
            # TODO: in future, add more info about where the existing function is registered (this info is
            # today already returned by the C++ warning when impl is called but we error out before that)
            raise RuntimeError(
                "This is not allowed since there's already a kernel registered from python overriding {}"
                "'s behavior for {} dispatch key and {} namespace.".format(
                    name.split("::")[-1], dispatch_key, self.ns
                )
            )

        if dispatch_key == "Meta":
            dispatcher_op_name = name
            if "::" not in dispatcher_op_name:
                dispatcher_op_name = f"{self.ns}::{dispatcher_op_name}"

            op = torch._library.utils.lookup_op(dispatcher_op_name)
            if torch._library.utils.is_out(op) and not torch._library.utils.is_builtin(
                op
            ):
                warnings.warn(
                    f"Registering a Meta kernel for operator '{dispatcher_op_name}' "
                    f"which has torch.Tag.out. Operators with Tag.out automatically "
                    f"get a fake kernel that returns the out= arguments. We "
                    f"recommend not registering a fake/meta kernel manually "
                    f"because it is easy to get wrong.",
                    stacklevel=2,
                )

            # Internally, we shouldn't be registering meta kernels for any operators that
            # have CompositeImplicitAutograd kernels.
            # Instead, we should be letting those decompositions run, and writing meta kernels
            # only for the base operators.
            if torch._C._dispatch_has_kernel_for_dispatch_key(
                dispatcher_op_name, "CompositeImplicitAutograd"
            ):
                raise RuntimeError(
                    f"We should not register a meta kernel directly to the operator '{name}',"
                    " because it has a CompositeImplicitAutograd kernel in core."
                    " Instead we should let the operator decompose, and ensure that we have meta kernels"
                    " for the base ops that it decomposes into."
                )

        if self.m is None:
            raise AssertionError("Library object has been destroyed")
        self.m.impl(
            name,
            dispatch_key if dispatch_key != "" else "CompositeImplicitAutograd",
            fn,
            with_keyset,
        )

        _impls.add(key)
        self._op_impls.add(key)