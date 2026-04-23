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