def fuzz_inputs_specs(self, output_spec: Spec, num_inputs: int = 3) -> list[Spec]:
        """Generate input specs for index_select operation.

        torch.index_select(input, dim, index) returns a tensor with:
        - output.shape[dim] = len(index)
        - output.shape[other_dims] = input.shape[other_dims]
        """
        if not isinstance(output_spec, TensorSpec):
            raise ValueError("IndexSelectOperator can only produce TensorSpec outputs")

        # For simplicity, we'll work with a 2D input tensor
        # and select along dimension 0
        dim = 0
        output_size = output_spec.size

        # Input tensor - create a shape where we can select from it
        # If output is (k, m), input can be (n, m) where n >= k
        if len(output_size) == 1:
            # Output is 1D, input should be at least 1D
            input_size = (output_size[0] + 2,)  # Make input larger
            input_stride = (1,)
        elif len(output_size) == 2:
            # Output is 2D, input should be 2D with first dim >= output first dim
            input_size = (output_size[0] + 2, output_size[1])
            input_stride = (output_size[1], 1)  # Contiguous
        else:
            # For higher dimensions, keep it simple
            input_size = tuple(
                s + 2 if i == dim else s for i, s in enumerate(output_size)
            )
            # Contiguous stride
            input_stride = tuple(
                int(torch.tensor(input_size[i + 1 :]).prod().item())
                if i < len(input_size) - 1
                else 1
                for i in range(len(input_size))
            )

        input_tensor_spec = TensorSpec(
            size=input_size,
            stride=input_stride,
            dtype=output_spec.dtype,
        )

        # Index tensor - 1D tensor of long dtype with indices
        index_spec = TensorSpec(
            size=(output_size[dim],) if len(output_size) > 0 else (1,),
            stride=(1,),
            dtype=torch.long,
        )

        return [input_tensor_spec, index_spec]