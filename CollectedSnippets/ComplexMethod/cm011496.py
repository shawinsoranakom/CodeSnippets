def analyze(
        self,
    ) -> tuple[Sequence[Placement], dict[int, list[int]]]:
        """Phase 1: walk the DimMap rule, return (input_tgt_placements, input_to_output_tensor_dims)."""
        input_dims_in_rule = self._input_dims_in_rule(self.rule)

        # Default: shardable if the dim appears in the rule. Refined by _analyze_*.
        for dim in range(len(self.global_input_shape)):
            self.shard_allowed[dim] = [dim in input_dims_in_rule] * self.mesh_ndim

        # Walk the rule to refine shard_allowed and build input_to_output_tensor_dims.
        #
        # Flatten example: view([2, 3, 4], [6, 4])
        #   rule = (Flatten(InputDim(0), InputDim(1)), InputDim(2))
        #   output_dim=0 (Flatten): hits the isinstance(cmd, Flatten) branch.
        #     Maps input dims 0 and 1 to output dim 0.  Result: {0: [0], 1: [0]}
        #   output_dim=1 (InputDim(2)): hits the len(in_dims) > 0 branch.
        #     Maps input dim 2 to output dim 1.  Result: {0: [0], 1: [0], 2: [1]}
        #
        # Split example: view([6], [2, 3])
        #   rule = (Split(InputDim(0), (2,3), 0), Split(InputDim(0), (2,3), 1))
        #   output_dim=0 (split_id=0): hits the len(in_dims) > 0 branch.
        #     Maps input dim 0 to output dim 0.  Result: {0: [0]}
        #   output_dim=1 (split_id=1): hits the isinstance(cmd, Split) branch
        #     because _analyze_split returns [] for split_id>0.  Chases root
        #     InputDim(0) and appends output dim 1.  Result: {0: [0, 1]}
        input_to_output_tensor_dims: dict[int, list[int]] = {}
        for output_dim, cmd in enumerate(self.rule):
            in_dims = self._analyze_dim(cmd)
            if isinstance(cmd, Flatten):
                for in_dim in in_dims:
                    if in_dim.input_dim in input_to_output_tensor_dims:
                        raise AssertionError(
                            f"Input dim {in_dim.input_dim} already mapped to output dims "
                            f"{input_to_output_tensor_dims[in_dim.input_dim]}"
                        )
                    input_to_output_tensor_dims[in_dim.input_dim] = [output_dim]
            elif len(in_dims) > 0:
                # InputDim (identity) or Split(split_id=0).
                in_dim = in_dims[0]
                if in_dim.input_dim not in input_to_output_tensor_dims:
                    input_to_output_tensor_dims[in_dim.input_dim] = [output_dim]
                else:
                    input_to_output_tensor_dims[in_dim.input_dim].append(output_dim)
            elif isinstance(cmd, Split):
                # Split(split_id>0): _analyze_split returned [], so chase the
                # root input dim and append this output dim to its existing entry.
                #
                # Flatten+Split example: view([2, 3], [3, 2])
                #   rule = (Split(Flatten(InputDim(0), InputDim(1)), (3,2), 0),
                #           Split(Flatten(InputDim(0), InputDim(1)), (3,2), 1))
                #   output_dim=0 (split_id=0): same as Split example above.
                #     Result: {0: [0]}
                #   output_dim=1 (split_id=1): same as Split example, but
                #     the chase unwraps the inner Flatten to find InputDim(0).
                #     Result: {0: [0, 1]}
                root_spec = cmd.input_dim
                while isinstance(root_spec, (Flatten, Split)):
                    if isinstance(root_spec, Flatten):
                        # _analyze_flatten always returns input_dims[0] as
                        # the first element (either as the only shardable dim
                        # in non-strict mode, or as the fallback when nothing
                        # is sharded), so split_id=0 uses it as the key in
                        # input_to_output_tensor_dims. Use [0] here to match.
                        root_spec = root_spec.input_dims[0]
                    else:
                        root_spec = root_spec.input_dim
                root = root_spec if isinstance(root_spec, InputDim) else None
                if root is not None and root.input_dim in input_to_output_tensor_dims:
                    input_to_output_tensor_dims[root.input_dim].append(output_dim)

        input_tgt_placements: list[Placement] = []
        for mesh_dim, p in enumerate(self.input_src_placements):
            if (
                isinstance(p, Shard | _StridedShard)
                and not self.shard_allowed[p.dim][mesh_dim]
            ):
                if self.strict_view:
                    raise RuntimeError(
                        f"This operation would remove or reshape sharded "
                        f"dimension {p.dim}, which requires redistribution. "
                        f"Please redistribute the input first."
                    )
                input_tgt_placements.append(Replicate())
            else:
                input_tgt_placements.append(p)
        return input_tgt_placements, input_to_output_tensor_dims