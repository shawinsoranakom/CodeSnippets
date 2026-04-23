def _codegen(
        self,
        wrapper: PythonWrapperCodegen,
        epilogue_fusion: tuple[ComputedBuffer, str] | None,
    ) -> None:
        """Overrides the parent member.
        See https://github.com/pytorch/pytorch/issues/151692"""

        from torch._inductor.utils import triton_version_uses_attrs_dict

        (
            kernel,
            configs,
            restore_value_args,
            reset_to_zero_args,
        ) = self.get_kernel_and_metadata()

        # Definition of kernel
        (
            new_name,
            triton_meta,
            inductor_meta,
            extra_launch_args,
        ) = wrapper.define_user_defined_triton_kernel(
            kernel,
            configs,
            self.kwargs,
            restore_value_args,
            reset_to_zero_args,
            self.grid,
            epilogue_fusion,
        )
        named_args = {
            k: self.get_kwargs_value(k) for k in self.ordered_kwargs_for_cpp_kernel
        }

        if epilogue_fusion:
            assert len(self.arg_accesses.read_writes.writes) == 1
            mutable_arg_name = next(iter(self.arg_accesses.read_writes.writes)).name
            assert mutable_arg_name in named_args
            epilogue_computed_buffer, _ = epilogue_fusion
            named_args[mutable_arg_name] = epilogue_computed_buffer

        arg_names = [p.name for p in kernel.params]  # type: ignore[attr-defined]
        constexprs = [p.num for p in kernel.params if p.is_constexpr]  # type: ignore[attr-defined]
        constexpr_names = OrderedSet(arg_names[i] for i in constexprs)

        args: list[Any] = []
        arg_types: list[Any] = []
        raw_keys_filtered: list[Any] = []
        raw_args_filtered: list[Any] = []
        for name, arg in itertools.chain(
            named_args.items(), zip(itertools.repeat(""), extra_launch_args)
        ):
            if name in constexpr_names and triton_version_uses_attrs_dict():
                # see #160000 - we don't pass in constexpr args to speed up runtime.
                continue
            raw_keys_filtered.append(name)
            raw_args_filtered.append(arg)
            if isinstance(arg, IRNode):
                args.append(arg.codegen_reference())
                arg_types.append(arg.get_dtype())
            elif isinstance(arg, (int, float, bool, sympy.Expr)):
                args.append(arg)
                arg_types.append(type(arg))
            elif name in constexpr_names:
                # insert a dummy value for constexpr args of unsupported type
                # constexprs will end up getting baked into the kernel at compile time
                args.append(-1)
                arg_types.append(int)
            elif arg is None:
                """
                Filter out None args.

                see https://github.com/pytorch/pytorch/issues/115344

                Two cases for a None arg:
                1. The arg is already tl.constexpr, so leave it in
                2. The arg is not tl.constexpr so we have to remove it
                """
                if triton_version_uses_attrs_dict():
                    args.append(-1)
                    arg_types.append(int)
                else:
                    raw_keys_filtered.pop()
                    raw_args_filtered.pop()
            else:
                raise NotImplementedError(f"Unsupported arg type: {type(arg)}: {arg}")

        self.codegen_comment(wrapper, new_name)
        wrapper.generate_kernel_call(
            new_name,
            args,
            arg_types=arg_types,
            raw_args=raw_args_filtered,
            raw_keys=raw_keys_filtered,
            triton_meta=triton_meta,
            inductor_meta=inductor_meta,
            triton=True,
            device=self.get_device(),
            original_fxnode_name=self.fx_node.name,
        )