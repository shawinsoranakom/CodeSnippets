def _analyze_flatten(self, cmd: Flatten) -> list[InputDim]:
        """Fill self.shard_allowed for Flatten; return sharded input dims."""
        from torch.fx.experimental.symbolic_shapes import guard_or_true

        sharded_dims: list[InputDim] = []
        num_input_dims = len(cmd.input_dims)
        for i, dim in enumerate(cmd.input_dims):
            if not isinstance(dim, InputDim):
                raise AssertionError(f"Expected InputDim, got {type(dim)}")
            shard_mesh_dim, shard_placement = self._find_plain_shard(dim)
            if shard_mesh_dim is None or shard_placement is None:
                continue  # default from analyze() already covers this
            tensor_dim_size = self.global_input_shape[shard_placement.dim]
            mesh_dim_size = self.mesh_sizes[shard_mesh_dim]
            can_shard_dim = True
            if self.strict_view:
                is_last_input_dim = i == num_input_dims - 1
                if not is_last_input_dim and guard_or_true(
                    tensor_dim_size % mesh_dim_size != 0
                ):
                    raise RuntimeError(
                        f"Cannot flatten unevenly sharded tensor: "
                        f"dimension {dim.input_dim} (size {tensor_dim_size}) "
                        f"is not evenly divisible by mesh dimension "
                        f"{shard_mesh_dim} (size {mesh_dim_size}). "
                        f"Please redistribute the tensor before this operation."
                    )
                sharded_dims.append(dim)
            else:
                # TODO: non-strict (reshape) should allow can_shard_dim = True
                # for non-first flatten dims, since strict_view already does.
                # Currently forces redistribution because the rewrite phase
                # wasn't originally implemented for this case.
                if i == 0:
                    sharded_dims.append(dim)
                    if guard_or_true(tensor_dim_size % mesh_dim_size != 0):
                        can_shard_dim = False
                else:
                    can_shard_dim = False
            self.shard_allowed[dim.input_dim] = [can_shard_dim] * self.mesh_ndim

        if len(sharded_dims) > 0:
            return sharded_dims
        # No sharded dims: e.g. Flatten([InputDim(0), InputDim(1)]) where
        # neither dim is sharded.  Return the first input dim so that
        # input_to_output_tensor_dims is populated for identity rewrites.
        if not isinstance(cmd.input_dims[0], InputDim):
            raise AssertionError(f"Expected InputDim, got {type(cmd.input_dims[0])}")
        return [cmd.input_dims[0]]