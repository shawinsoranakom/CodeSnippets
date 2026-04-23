def handle_single_output(
            return_type: torch.TensorType | torch.ListType | torch.JitType,
            output: IRNode | Sequence[IRNode],
        ) -> export_schema.Argument:
            if isinstance(return_type, (torch.TensorType, torch.NoneType)):
                # For single Tensor or None
                out = output
                if isinstance(output, (list, tuple)):
                    assert len(output) == 1
                    out = output[0]
                if isinstance(return_type, torch.TensorType):
                    assert isinstance(out, IRNode)
                    return export_schema.Argument.create(
                        as_tensor=export_schema.TensorArgument(name=out.get_name())
                    )
                else:  # NoneType
                    assert out is None
                    return export_schema.Argument.create(as_none=True)
            elif isinstance(return_type, torch.ListType) and isinstance(
                return_type.getElementType(), torch.TensorType
            ):
                assert isinstance(output, Sequence), type(output)
                # For single TensorList
                return export_schema.Argument.create(
                    as_tensors=[
                        export_schema.TensorArgument(name=out.get_name())
                        for out in output
                    ]
                )
            elif isinstance(return_type, torch.OptionalType) and isinstance(
                return_type.getElementType(), torch.TensorType
            ):
                # For OptionalTensor
                if output is None:
                    return export_schema.Argument.create(
                        as_optional_tensor=export_schema.OptionalTensorArgument.create(
                            as_none=True
                        )
                    )
                else:
                    assert isinstance(output, IRNode)
                    return export_schema.Argument.create(
                        as_optional_tensor=export_schema.OptionalTensorArgument.create(
                            as_tensor=export_schema.TensorArgument(
                                name=output.get_name()
                            )
                        )
                    )
            elif isinstance(return_type, torch.IntType):
                return export_schema.Argument.create(as_int=output)
            else:
                raise RuntimeError(f"Unsupported return type {type(return_type)}")