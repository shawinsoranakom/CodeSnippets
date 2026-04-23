def export_extern_kernel_node(self):  # type: ignore[no-untyped-def]
        """
        ProxyExecutor Design Note
        We export the ExternFallbackNodes (for custom ops) into a serialized file
        and run it with a host side proxy executor to address the ABI problem
        This is currently only implemented for fbcode. Eventually, we will also make this work for OSS.
        Detailed design doc can be found at
        https://docs.google.com/document/d/1wC4DOZFaYym2t1Esz0X5yxlLI3RDnSiyRbUus3bkJ64/edit?usp=sharing
        """
        log.debug(
            "Extern kernel node added for node %s with target %s.",
            self.get_name(),
            self.op_overload,
        )

        assert isinstance(self, FallbackKernel), type(self)
        args, kwargs = self.unflatten_args(self.inputs, self.constant_args)
        args = self.fill_non_provided_args(args, kwargs)
        ordered_kwargs = [
            self.get_kwargs_value(key, **kwargs)
            for key in self.ordered_kwargs_for_cpp_kernel
        ]
        target = self.op_overload

        if not V.graph.aot_mode:
            # No need to serialize in the cpp wrapper JIT mode
            return [*args, *ordered_kwargs]

        serializer = GraphModuleSerializer(None, [])  # type: ignore[arg-type]
        named_arguments = serializer.serialize_inputs(target, args, kwargs)

        # serialize_outputs
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

        if isinstance(target, torch._higher_order_ops.torchbind.CallTorchBind):
            returns = target.schema(args[0], args[1]).returns
        else:
            returns = target._schema.returns  # type: ignore[union-attr]
        if len(returns) == 1:
            # NOTE: [special handling of all_reduce_coalesced_'s return value]
            # all_reduce_coalesced_ return a list of tensors via self.mutation_outputs
            outputs = self.outputs if self.outputs else self.mutation_outputs
            return_type = returns[0].real_type
            output_arguments = [handle_single_output(return_type, outputs)]
        else:
            # For tuple returns, e.g "-> (Tensor, Tensor)" or "-> (Tensor, Tensor[])"
            # Not generating output args for self.mutation_outputs
            output_arguments = [
                handle_single_output(
                    return_schema.real_type,  # type: ignore[attr-defined]
                    output,
                )
                for return_schema, output in zip(returns, self.outputs)
            ]

        assert self.op_overload is not None
        node = ExternKernelNode(
            name=self.get_name(),
            node=export_schema.Node(
                target=self.op_overload.name(),
                inputs=named_arguments,
                outputs=output_arguments,
                metadata={},
            ),
        )

        V.extern_kernel_nodes.append(node)

        return [*args, *ordered_kwargs]