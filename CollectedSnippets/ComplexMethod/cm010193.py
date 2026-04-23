def serialize_outputs(self, node: torch.fx.Node) -> list[Argument]:
        """For a given node, return the dataclass representing its output values.

        [NOTE: Multiple outputs] We handle aggregates differently than FX. For
        FX, it looks like:

            x = call_function("multiple_return", ...)
            element0 = call_function(getitem, x, 0)
            foo = call_function("use_output", element0)

        We do not want the intermediate `getitem` call, so our serialized thing looks like:

            element0, element1, element2 = call_function("multiple_return", ...)
            foo = call_function("use_output", element0)

        We want names to be consistent across these two schemes, so that we can
        mostly reuse the names coming from FX. This function computes a mapping from
        the FX representation to our representation, preserving the names.
        """

        def _is_single_tensor_list_return(target: Any) -> bool:
            schema = _get_schema_from_target(target)
            returns = schema.returns

            if len(returns) != 1:
                return False
            return_type = returns[0].real_type
            return isinstance(return_type, torch.ListType) and isinstance(
                return_type.getElementType(), torch.TensorType
            )

        if not (
            node.op == "call_function"
            and isinstance(
                node.target, (torch._ops.OpOverload, *_registered_extension_types())
            )
        ):
            raise AssertionError(
                f"expected call_function with OpOverload or registered extension type, "
                f"got {node.op} with {type(node.target).__name__}"
            )

        schema = _get_schema_from_target(node.target)
        returns = schema.returns

        if len(returns) == 0:
            return []

        meta_val = node.meta["val"]

        # Check single value return
        if _is_single_tensor_list_return(node.target):
            # e.g "-> Tensor[]"
            tensor_args = []
            for idx, meta in enumerate(meta_val):
                name = self._output_node_name_at_index(node, idx)
                tensor_args.append(self.serialize_tensor_output(name, meta))
            return [Argument.create(as_tensors=tensor_args)]
        elif len(returns) == 1:
            return [self.serialize_output(node.name, meta_val)]

        # There are a two possibilities at this point:
        # - This operator returns a tuple of Tensors, e.g. "-> (Tensor, Tensor)"
        # - This operator returns a tuple of mixed of Tensor and Tensors, e.g. "-> (Tensor, Tensor[])"
        #
        # Either way, start by gathering a list of TensorArguments with the correct names.
        # For consistent naming with FX, consult the downstream `getitem` node and
        # make sure our outputs have the same name.

        output_arguments = []
        for idx, (meta, return_schema) in enumerate(zip(meta_val, returns)):
            if meta is None:
                if not isinstance(
                    return_schema.real_type, (torch.OptionalType, torch.TensorType)
                ):
                    raise AssertionError(
                        f"expected OptionalType or TensorType, got {type(return_schema.real_type).__name__}"
                    )
                # When the return type is annotated as Tensor type, the op can also return an
                # undefined Tensor which will be implicitly converted to None in Python.
                output_arguments.append(Argument.create(as_none=True))
            elif isinstance(meta, FakeTensor):
                if not isinstance(
                    return_schema.real_type, (torch.OptionalType, torch.TensorType)
                ):
                    raise AssertionError(
                        f"expected OptionalType or TensorType, got {type(return_schema.real_type).__name__}"
                    )
                name = self._output_node_name_at_index(node, idx)
                output_arguments.append(self.serialize_output(name, meta))
            elif isinstance(meta, list):
                # for List[Tensor] return type
                if not (
                    isinstance(return_schema.real_type, torch.ListType)
                    and isinstance(
                        return_schema.real_type.getElementType(), torch.TensorType
                    )
                ):
                    raise AssertionError(
                        f"expected ListType with TensorType element, got {type(return_schema.real_type).__name__}"
                    )
                user_node = self._output_node_at_index(node, idx)
                args = []
                for i, m in enumerate(meta):
                    if m is None:
                        continue
                    if user_node is None:
                        name = f"{node.name}_unused_{idx}_{i}"
                    else:
                        name = self._output_node_name_at_index(user_node, i)
                    args.append(self.serialize_tensor_output(name, m))
                output_arguments.append(Argument.create(as_tensors=args))
            elif isinstance(meta, (int, SymInt, float, SymFloat)):
                user_node_name = self._output_node_name_at_index(node, idx)
                output_arguments.append(self.serialize_output(user_node_name, meta))
            else:
                raise ValueError(
                    f"Unhandled output type {type(meta)} from node {node.format_node()}"
                )

        return output_arguments