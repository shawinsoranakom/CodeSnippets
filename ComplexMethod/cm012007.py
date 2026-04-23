def __init__(
        self,
        layout: OutputSpec,
        kernel: _OpOverloads,
        tensor_args: Sequence[IRNode],
        nontensor_args: Sequence[Any],
        unflatten_args: Callable[..., Any],
        kwargs: dict[str, Any] | None = None,
        *,
        unbacked_bindings: dict[sympy.Symbol, pytree.KeyPath] | None = None,
    ) -> None:
        super().__init__(
            layout,
            tuple(tensor_args),
            tuple(nontensor_args),
            op_overload=kernel,
        )

        self.use_runtime_dispatch = False
        self.unbacked_bindings = unbacked_bindings or {}

        assert isinstance(
            kernel, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)
        ), f"Fails to create FallbackKernel for {kernel}: {type(kernel)} not supported"
        self.op_overload = kernel
        self.unflatten_args = unflatten_args
        self.kwargs = {} if kwargs is None else kwargs
        assert self.python_kernel_name is not None
        V.graph.warn_fallback(self.python_kernel_name)

        # args that are aliased
        self.alias_names: list[str] = []
        # args that are mutated AND returned from the op
        self.mutation_names: list[str] = []

        if isinstance(self.op_overload, torch._ops.HigherOrderOperator):
            # We assume here that HOPs with FallbackKernel are functional.
            # This may not always be true! HOPs must individually opt-in to
            # FallbackKernel, so please check this if you opt-in.
            return

        if "_c10d_functional" in self.op_overload.name():
            # _c10d_functional kernels are lowered into _CollectiveKernel which
            # derives from FallbackKernel for the cpp codegen. The kernels
            # don't pass the can_auto_functionalize check, but their mutation
            # is handled properly by _CollectiveKernel.
            return

        schema = self.op_overload._schema

        # NOTE: [FallbackKernel supported operators]
        # We only support three types of operators:
        # - functional ops
        # - view ops
        # - inplace aten ops
        # - mutating ops that are auto-functionalizable. That is,
        # the operator may mutate any number of inputs, but its outputs
        # may not alias any of the inputs.
        #
        # The unsupported cases usually do not show up here (because
        # AOTAutograd functionalized them away); the only way for an in-place
        # op to show up here is if a lowering or pass introduced it.
        if torch._library.utils.mutates_and_returns_first_arg(self.op_overload):
            self.mutation_names.append(tensor_args[0].get_name())
            return

        def has_functionalize_impl(op: torch._ops.OpOverload) -> bool:
            return torch._C._dispatch_has_kernel_for_dispatch_key(
                op.name(), torch._C.DispatchKey.Functionalize
            ) or (
                hasattr(op, "py_kernels")
                and torch._C.DispatchKey.Functionalize in op.py_kernels
            )

        if (
            schema.is_mutable
            and not can_auto_functionalize(self.op_overload)
            and not has_functionalize_impl(self.op_overload)
        ):
            raise NotImplementedError(
                f"NYI: Can't generate FallbackKernel for {self.op_overload}"
            )

        args, kwargs = self.unflatten_args(self.inputs, self.constant_args)

        def handle_aliasing_and_mutation(info: torch._C.Argument, arg: Any) -> None:
            # Assertions to make sure we didn't mismatch args
            if isinstance(info.type, torch.ListType):
                assert isinstance(arg, (list, tuple)), type(arg)
            if library_utils.is_tensor_like_type(info.type):
                # PyTorch also accepts None and scalar types for args marked as "Tensor".
                # We're not going to check all of them here.
                assert not isinstance(arg, (tuple, list))

            if arg is None:
                return
            if info.alias_info is None:
                return

            def add_alias(t: IRNode) -> None:
                self.alias_names.append(t.get_name())
                assert info.alias_info is not None
                if info.alias_info.is_write:
                    self.mutation_outputs.append(
                        MutationOutput(NoneLayout(device=t.get_device()), t, self)
                    )

            if library_utils.is_tensorlist_like_type(info.type):
                if arg is not None:
                    for optional_tensor_arg in arg:
                        add_alias(optional_tensor_arg)
            else:
                assert library_utils.is_tensor_like_type(info.type)

                add_alias(arg)

        for info, arg in torch._library.utils.zip_schema(schema, args, kwargs):
            handle_aliasing_and_mutation(info, arg)