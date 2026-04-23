def args_codegen(self, arg_operations):
        """Generate argument creation code for default template."""
        code_lines = []

        # Add sentinel tensor that ensures gradient computation
        code_lines.extend(
            [
                "# Sentinel tensor to ensure gradient computation",
                "sentinel = torch.tensor(1.0, requires_grad=True)",
                "",
            ]
        )

        if arg_operations:
            for i, (node_id, spec) in enumerate(arg_operations):
                arg_name = f"arg_{i}"

                if isinstance(spec, ScalarSpec):
                    dtype_str = f"torch.{spec.dtype}".replace("torch.torch.", "torch.")
                    if spec.dtype in [
                        torch.int8,
                        torch.int16,
                        torch.int32,
                        torch.int64,
                    ]:
                        # For integer scalars, use randint to avoid always getting 0
                        code_lines.append(
                            f"{arg_name} = int(torch.randint(5, 30, ()).item())"
                        )
                    elif spec.dtype == torch.bool:
                        # For boolean scalars, use randint and cast to bool
                        code_lines.append(
                            f"{arg_name} = bool(torch.randint(0, 2, ()).item())"
                        )
                    else:
                        # For float scalars, use randn
                        code_lines.append(
                            f"{arg_name} = float(torch.randn((), dtype={dtype_str}).item())"
                        )

                elif isinstance(spec, TensorSpec):
                    size_str = str(spec.size)
                    dtype_str = f"torch.{spec.dtype}".replace("torch.torch.", "torch.")

                    # Calculate storage size needed for the strided tensor
                    if spec.size:
                        # Calculate the maximum index that will be accessed
                        max_offset = 0
                        for dim_size, stride in zip(spec.size, spec.stride):
                            if dim_size > 1:
                                max_offset += (dim_size - 1) * abs(stride)
                        storage_size = max_offset + 1
                    else:
                        storage_size = 1

                    stride_str = str(spec.stride)

                    # Special handling for integer tensors which might be used as indices
                    if spec.dtype in [
                        torch.int8,
                        torch.int16,
                        torch.int32,
                        torch.int64,
                    ]:
                        # For integer tensors, generate valid indices with headroom for arithmetic
                        # Use smaller range [5, 30] to allow for multiplication and other operations
                        # This prevents indices from becoming too large after arithmetic
                        min_val = (
                            5  # Minimum to avoid negative results after subtraction
                        )
                        max_val = (
                            30  # Maximum to avoid out-of-bounds after multiplication
                        )
                        code_lines.append(
                            f"{arg_name} = torch.as_strided(torch.randint({min_val}, {max_val}, ({storage_size},)).to({dtype_str}), {size_str}, {stride_str})"
                        )
                    elif spec.dtype == torch.bool:
                        # For boolean tensors, use randint to generate True/False values
                        # Using randn().to(bool) would yield almost all True due to non-zero floats
                        code_lines.append(
                            f"{arg_name} = torch.as_strided(torch.randint(0, 2, ({storage_size},), dtype=torch.int8).bool(), {size_str}, {stride_str})"
                        )
                    else:
                        code_lines.append(
                            f"{arg_name} = torch.as_strided(torch.randn({storage_size}).to({dtype_str}), {size_str}, {stride_str})"
                        )

        return code_lines