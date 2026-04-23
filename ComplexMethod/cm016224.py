def args_codegen(self, arg_operations, constant_operations=None):
        """Generate args with randomized placements using dist_tensor API."""

        code_lines = []

        # DTensor setup (same as parent)
        code_lines.extend(
            [
                "world_size = 1024",
                "fake_store = FakeStore()",
                "torch.distributed.init_process_group(",
                '    "fake", store=fake_store, rank=0, world_size=world_size',
                ")",
                "",
                "mesh = torch.distributed.device_mesh.init_device_mesh(",
                '    "cuda", (2, 8), mesh_dim_names=("dim1", "dim2")',
                ")",
                "",
            ]
        )

        # Sentinel with random placement
        sentinel_placements = self._generate_random_placement((1,))
        code_lines.extend(
            [
                f"sentinel = dist_tensor.ones((1,), device_mesh=mesh, placements={sentinel_placements}, dtype=torch.float32, requires_grad=True)",
                "",
            ]
        )

        # Args with random placements using dist_tensor API
        if arg_operations:
            for i, (node_id, spec) in enumerate(arg_operations):
                if isinstance(spec, TensorSpec):
                    size_str = str(spec.size)
                    dtype_str = f"torch.{spec.dtype}".replace("torch.torch.", "torch.")
                    placements = self._generate_random_placement(spec.size)

                    if spec.dtype in [
                        torch.int32,
                        torch.int64,
                        torch.int8,
                        torch.int16,
                    ]:
                        code_lines.append(
                            f"arg_{i} = dist_tensor.ones({size_str}, device_mesh=mesh, placements={placements}, dtype={dtype_str}) * 5"
                        )
                    elif spec.dtype == torch.bool:
                        code_lines.append(
                            f"arg_{i} = dist_tensor.ones({size_str}, device_mesh=mesh, placements={placements}, dtype=torch.int8).bool()"
                        )
                    else:
                        code_lines.append(
                            f"arg_{i} = dist_tensor.randn({size_str}, device_mesh=mesh, placements={placements}, dtype={dtype_str}, requires_grad=True)"
                        )

        # Constants (if any) - use same dist_tensor approach
        if constant_operations:
            for node_id, var_name, spec in constant_operations:
                if isinstance(spec, TensorSpec):
                    size_str = str(spec.size)
                    dtype_str = f"torch.{spec.dtype}".replace("torch.torch.", "torch.")
                    placements = self._generate_random_placement(spec.size)
                    # Use dist_tensor.full with a simple fill value
                    code_lines.append(
                        f"{var_name} = dist_tensor.full({size_str}, 1.0, device_mesh=mesh, placements={placements}, dtype={dtype_str})"
                    )

        code_lines.append("")
        return code_lines