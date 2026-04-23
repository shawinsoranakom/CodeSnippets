def generate_extern_kernel_args_decl_if_needed(
        self,
        op_overload: torch._ops.OpOverload | torch._ops.HigherOrderOperator,
        raw_args: Sequence[Any],
        output_args: _OUTPUT_ARGS_TYPE,
        raw_outputs: Sequence[ir.Buffer],
    ):
        """
        Generates declarations for external kernel arguments if needed, based on the provided
        operator and its arguments. It processes both input and output arguments, categorizing
        them into tensor and integer arguments for further code generation.
        """
        schema = None
        if isinstance(op_overload, torch._higher_order_ops.torchbind.CallTorchBind):
            obj = raw_args[0]
            method = raw_args[1]
            schema = op_overload.schema(obj, method)
        else:
            assert isinstance(op_overload, torch._ops.OpOverload), type(op_overload)
            schema = op_overload._schema
        assert schema is not None
        arg_types = [x.real_type for x in schema.arguments]
        return_types = [x.type for x in schema.returns]

        new_tensor_args = []
        new_int_args = []

        def fill_args(arg, arg_type):
            static_arg_types = (
                torch.FloatType,
                torch.BoolType,
                torch.StringType,
                torch.Type,
                torch.DeviceObjType,
            )
            inductor_tensor_buffers = (
                ir.Buffer,
                ir.ReinterpretView,
            )

            if isinstance(arg_type, torch.TensorType):
                assert isinstance(arg, inductor_tensor_buffers), f"got {type(arg)}"
                new_tensor_args.append(f"{arg.codegen_reference()}")
            elif isinstance(arg_type, torch.IntType):
                # int
                new_int_args.append(str(arg))
            elif isinstance(arg_type, torch.SymIntType):
                # SymInt
                expr = arg.node.expr if isinstance(arg, torch.SymInt) else arg
                new_int_args.append(cexpr(expr))
            elif isinstance(arg_type, torch.NumberType):
                # Scalar of type int
                assert isinstance(arg, (int, float, bool))
                # Only treat int Scalar as dynamic
                if isinstance(arg, int):
                    new_int_args.append(str(arg))
            elif isinstance(arg, ir.TorchBindObject):
                # torchbind objects are loaded in proxy executor
                pass
            elif isinstance(arg_type, torch.ListType):
                assert isinstance(arg, (list, tuple))

                # List[Tensor]
                if isinstance(arg_type.getElementType(), torch.TensorType):
                    new_tensor_args.extend([f"{a.codegen_reference()}" for a in arg])
                # List[Optional[Tensor]]
                elif isinstance(
                    arg_type.getElementType(), torch.OptionalType
                ) and isinstance(
                    arg_type.getElementType().getElementType(), torch.TensorType
                ):
                    new_tensor_args.extend(
                        [f"{a.codegen_reference()}" for a in arg if a is not None]
                    )
                # List[int]
                elif isinstance(arg_type.getElementType(), torch.IntType):
                    new_int_args.extend([str(a) for a in arg])
                # List[SymInt]
                elif isinstance(arg_type.getElementType(), torch.SymIntType):
                    expressions = [
                        a.node.expr if isinstance(a, torch.SymInt) else a for a in arg
                    ]
                    new_int_args.extend([cexpr(expr) for expr in expressions])
                # List[Scalar]
                elif isinstance(arg_type.getElementType(), torch.NumberType):
                    # Only treat int Scalar as dynamic
                    is_int_type = [isinstance(a, int) for a in arg]
                    if any(is_int_type):
                        assert all(is_int_type), (
                            "AOTInductor only supports int scalars of the same type"
                        )
                        new_int_args.extend([str(a) for a in arg])
                else:
                    assert isinstance(
                        arg_type.getElementType(),
                        static_arg_types,  # type: ignore[arg-type]
                    ), (
                        f"Fall through arguments must be one of static_arg_types, got {type(arg_type)}"
                    )
            else:
                assert isinstance(
                    arg_type,
                    static_arg_types,  # type: ignore[arg-type]
                ), (
                    f"Fall through arguments must be one of static_arg_types, got {type(arg_type)}"
                )

        for arg, arg_type in zip(raw_args, arg_types):
            if arg is not None:
                if isinstance(arg_type, torch.OptionalType):
                    fill_args(arg, arg_type.getElementType())
                else:
                    fill_args(arg, arg_type)

        def fill_output_arg(
            arg: str, return_type: torch.JitType, is_mutated_output: bool
        ) -> None:
            if isinstance(return_type, torch.TensorType):
                if not is_mutated_output:
                    self.writeline(f"AtenTensorHandle {arg}_handle;  // output buffer")
                    self.writeline(
                        f"AOTI_TORCH_ERROR_CODE_CHECK(aoti_torch_new_uninitialized_tensor(&{arg}_handle));"
                    )
                    self.writeline(f"RAIIAtenTensorHandle {arg}({arg}_handle);")
                new_tensor_args.append(f"{arg}")
            elif isinstance(return_type, torch.SymIntType):
                raise NotImplementedError("NYI support for return type: SymInt")
            elif isinstance(return_type, torch.ListType) and isinstance(
                return_type.getElementType(), torch.SymIntType
            ):
                raise NotImplementedError("NYI support for return type: List[SymInt]")
            else:
                raise AssertionError(f"Unsupported return type found: {return_type}")

        # TODO: Only support None and tensor(s) returns for now, SymInt is not implemented yet
        for return_type in return_types:
            if isinstance(
                return_type, (torch.TensorType, torch.NoneType, torch.IntType)
            ):
                pass
            elif isinstance(return_type, torch.OptionalType):
                assert isinstance(return_type.getElementType(), torch.TensorType)
            elif isinstance(return_type, torch.ListType):
                assert isinstance(return_type.getElementType(), torch.TensorType)
            else:
                raise NotImplementedError(
                    f"return type {return_type} is not yet supported."
                )

        for output_arg, raw_output_arg in zip(output_args, raw_outputs):  # type: ignore[arg-type]
            # None output is supported, but Optional return types are not yet supported
            if output_arg is None:
                continue
            elif isinstance(raw_output_arg, int):
                new_int_args.append(str(raw_output_arg))
            elif isinstance(output_arg, list):
                for out in output_arg:
                    assert out is not None, out
                    fill_output_arg(
                        out,
                        torch.TensorType.get(),
                        isinstance(raw_output_arg, ir.MutationOutput),
                    )
            else:
                fill_output_arg(
                    output_arg,
                    torch.TensorType.get(),
                    isinstance(raw_output_arg, ir.MutationOutput),
                )

        return new_tensor_args, new_int_args