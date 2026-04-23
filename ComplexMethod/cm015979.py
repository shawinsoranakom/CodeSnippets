def _run_and_format_categories(self, fn, indent=12):
        """Generate summary of assigned categories for expecttest."""

        # Use `__torch_dispatch__` to collect ground truth.
        with RecordInputOutputDispatchMode() as record_ops, profile() as prof:
            fn(lambda name: record_ops.mark_region(f"-- {name} ".ljust(105, "-")))

        memory_profile = prof._memory_profile()
        ptr_pair_to_key: dict[tuple[int, int], _memory_profiler.TensorKey] = {}
        snapshot = memory_profile._category_snapshot()

        # Build map from observed live Tensors to the memory profiler's
        # TensorKey representation.
        for op in memory_profile._op_tree.dfs():
            if op.typed[0] == _EventType.TorchOp:
                inputs = pytree.tree_leaves(op.typed[1].inputs)
                for t in (i for i in inputs if isinstance(i, _TensorMetadata)):
                    key = _memory_profiler.TensorKey.from_tensor(t)
                    if key:
                        ptr_pair_to_key[(t.impl_ptr, t.storage_data_ptr)] = key

        def format_categories(ptr_pair: int):
            target_key = ptr_pair_to_key.get(ptr_pair)
            if target_key is None:
                return "???"

            matches = tuple(
                (version, category.name if category else "???")
                for (key, version), category in snapshot.items()
                if key == target_key
            )
            if not matches:
                raise AssertionError("Failed to lookup Tensor")

            # Deduplicate version bumps which don't change the category.
            categories = [matches[0][1]]
            for _, category in matches:
                if category != categories[-1]:
                    categories.append(category)

            return f"{target_key.storage.allocation_id} ({','.join(categories)})"

        out: list[str] = []
        for name, inputs, outputs in record_ops.results:
            if inputs or outputs:
                # PyTorch ops
                inputs_str = ", ".join(format_categories(i) for i in inputs)
                outputs_str = ", ".join(format_categories(i) for i in outputs)
                out.append(f"{name:<40} {inputs_str:<45} -> {outputs_str}")

            else:
                # Marked regions.
                out.append(f"\n{name}")

        return textwrap.indent("\n".join(out), " " * indent)