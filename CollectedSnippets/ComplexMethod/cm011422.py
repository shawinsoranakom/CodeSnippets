def _get_candidate_placements(
        op_schema: OpSchema,
    ) -> list[tuple[Placement | None]]:
        tensor_specs = _extract_input_specs(op_schema)
        flat_specs, _ = tree_flatten(list(tensor_specs))

        # Step 1: Collect unique placements across all DTensorSpec inputs
        all_placements: set[Placement] = {Replicate()}
        tree_map_only(
            DTensorSpec,
            lambda spec: all_placements.update(spec.placements),
            flat_specs,
        )

        # Step 2: For each input, use the placement set, but expand Shard/StridedShard to all tensor dims
        candidates: list[list[Placement | None]] = []
        for spec in flat_specs:
            if not isinstance(spec, DTensorSpec):
                candidates.append([None])
            else:
                options = set(all_placements)
                for p in all_placements:
                    if isinstance(p, _StridedShard):
                        options |= {
                            _StridedShard(i, split_factor=p.split_factor)
                            for i in range(spec.ndim)
                        }
                    elif isinstance(p, Shard):
                        options |= {Shard(i) for i in range(spec.ndim)}
                candidates.append(list(options))

        # pyrefly: ignore [bad-argument-type, no-matching-overload]
        return list(itertools.product(*candidates))