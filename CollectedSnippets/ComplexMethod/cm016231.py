def codegen(
        self, output_name: str, input_names: list[str], output_spec: Spec
    ) -> str:
        """Generate code for group_norm operation."""
        if len(input_names) < 1 or len(input_names) > 3:
            raise ValueError(
                "GroupNorm requires 1-3 inputs: input, optional weight, optional bias"
            )

        if not isinstance(output_spec, TensorSpec):
            raise ValueError("GroupNormOperator can only produce TensorSpec outputs")

        target_dtype = str(output_spec.dtype)
        input_name = input_names[0]

        # Determine number of groups (must divide num_channels evenly)
        num_channels = output_spec.size[1]
        # Common choices: 32, 16, 8, or equal to channels (instance norm)
        possible_groups = [g for g in [32, 16, 8, 4, 2, 1] if num_channels % g == 0]
        num_groups = possible_groups[0] if possible_groups else 1

        if len(input_names) == 1:
            return f"{output_name} = torch.nn.functional.group_norm({input_name}.to({target_dtype}), {num_groups})"
        elif len(input_names) == 2:
            weight_name = input_names[1]
            return f"{output_name} = torch.nn.functional.group_norm({input_name}.to({target_dtype}), {num_groups}, weight={weight_name}.to({target_dtype}))"
        else:  # len(input_names) == 3
            weight_name = input_names[1]
            bias_name = input_names[2]
            return f"{output_name} = torch.nn.functional.group_norm({input_name}.to({target_dtype}), {num_groups}, weight={weight_name}.to({target_dtype}), bias={bias_name}.to({target_dtype}))"