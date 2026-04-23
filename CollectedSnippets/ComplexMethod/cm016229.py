def fuzz_inputs_specs(self, output_spec: Spec) -> list[Spec]:
        """Generate input spec for flatten operation."""
        if not isinstance(output_spec, TensorSpec):
            raise ValueError("FlattenOperator can only produce TensorSpec outputs")

        # Calculate total number of elements in output
        output_numel = 1
        for dim in output_spec.size:
            output_numel *= dim

        # Generate a multi-dimensional input that can be flattened
        if len(output_spec.size) == 1:
            # For 1D output, generate any multi-dimensional input
            input_size = fuzz_tensor_size()
            # Ensure input has multiple dimensions
            if len(input_size) < 2:
                input_size = (2, 2)  # Default multi-dim shape
        else:
            # For 2D output, generate input with more dimensions
            input_size = fuzz_tensor_size()
            if len(input_size) < 3:
                input_size = (2, 2, 2)  # Default 3D shape

        # Adjust input size to match output element count
        input_numel = 1
        for dim in input_size:
            input_numel *= dim

        if input_numel != output_numel:
            # Handle zero-sized tensors specially
            if output_numel == 0:
                # For zero-sized output, create zero-sized input
                input_size = tuple(list(input_size)[:-1] + [0])
            elif len(input_size) > 0 and output_numel > 0:
                # Calculate input shape that gives exactly output_numel elements
                prefix_numel = 1
                for dim in input_size[:-1]:
                    prefix_numel *= dim

                if prefix_numel > 0:
                    last_dim = output_numel // prefix_numel
                    # Ensure we get exactly output_numel elements
                    if last_dim * prefix_numel == output_numel:
                        input_size = tuple(list(input_size)[:-1] + [last_dim])
                    else:
                        # Fallback: create a simple shape with exact element count
                        input_size = (output_numel,)
                else:
                    input_size = (output_numel,)

        # Create input tensor spec
        from torchfuzz.tensor_fuzzer import fuzz_valid_stride

        input_stride = fuzz_valid_stride(tuple(input_size))

        return [
            TensorSpec(
                size=tuple(input_size), stride=input_stride, dtype=output_spec.dtype
            )
        ]