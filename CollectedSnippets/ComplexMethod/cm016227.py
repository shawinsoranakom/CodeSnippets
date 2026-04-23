def fuzz_inputs_specs(self, output_spec: Spec) -> list[Spec]:
        """Generate input spec for view operation."""
        if not isinstance(output_spec, TensorSpec):
            raise ValueError("ViewOperator can only produce TensorSpec outputs")

        # Calculate total number of elements in output
        output_numel = 1
        for dim in output_spec.size:
            output_numel *= dim

        # Generate a compatible input shape with exactly the same number of elements
        input_size = fuzz_tensor_size()

        # Always ensure exact element count match
        if output_numel == 0:
            # For zero-sized output, create zero-sized input
            input_size = tuple(list(input_size)[:-1] + [0])
        else:
            # Calculate input shape that gives exactly output_numel elements
            # Try to use the fuzzed shape structure but adjust to match element count
            if len(input_size) > 1:
                # Keep all dims except last, adjust last to make total = output_numel
                prefix_numel = 1
                for dim in input_size[:-1]:
                    prefix_numel *= dim

                if prefix_numel > 0 and output_numel % prefix_numel == 0:
                    last_dim = output_numel // prefix_numel
                    input_size = tuple(list(input_size)[:-1] + [last_dim])
                else:
                    # Fallback: create a simple shape with exact element count
                    input_size = (output_numel,)
            else:
                # For single-dim input, just use the exact element count
                input_size = (output_numel,)

        # Create input tensor spec with contiguous stride for view compatibility
        # .view() requires compatible memory layout, so use contiguous stride
        input_stride = tuple()
        if input_size:
            # Calculate contiguous stride
            stride = [1]
            for i in range(len(input_size) - 1, 0, -1):
                stride.insert(0, stride[0] * input_size[i])
            input_stride = tuple(stride)

        return [
            TensorSpec(size=input_size, stride=input_stride, dtype=output_spec.dtype)
        ]