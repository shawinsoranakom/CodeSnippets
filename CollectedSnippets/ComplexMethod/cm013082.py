def eval(
        self,
        schema: onnx.defs.OpSchema,
        args: Sequence[AllowedArgType],  # type: ignore[override]
        kwargs: Mapping[str, AllowedArgType],
    ) -> _tensors.SymbolicTensor | Sequence[_tensors.SymbolicTensor]:
        try:
            op_signature = ir.schemas.OpSignature.from_op_schema(schema)
            named_inputs, named_attrs = _construct_named_inputs_and_attrs(
                op_signature, args, kwargs
            )
            # TODO(justinchuby): Handle cast
            if schema.name == "CastLike":
                if len(named_inputs) != 2:
                    raise AssertionError(f"Expected 2 inputs, got {len(named_inputs)}")
                # Skip CastLike if the input and output types are the same
                src_input = named_inputs["input"]
                target_type = named_inputs["target_type"]

                if (
                    isinstance(src_input, ir.Value)
                    and isinstance(target_type, ir.Value)
                    and src_input.dtype is not None
                    and target_type.dtype is not None
                ):
                    # dtypes are available
                    if src_input.dtype == target_type.dtype:
                        # Same type. No cast needed
                        return src_input  # type: ignore[return-value]
                    else:
                        # Create a Cast node
                        return self.opset.Cast(src_input, to=target_type.dtype)  # type: ignore[union-attr,return-value]

            num_outputs = _determine_output_number(op_signature, named_attrs)
            outputs = self._call_op(
                op_signature, named_inputs, named_attrs, num_outputs
            )
            if len(outputs) == 1:
                return outputs[0]
            return outputs
        except Exception as e:
            raise _errors.GraphConstructionError(
                f"Error calling operator '{schema.name}' with args {args} and kwargs {kwargs}."
            ) from e