def call_tree_map_with_path_branch(
        self,
        tx: "InstructionTranslator",
        tree_map_fn: "UserFunctionVariable",
        map_fn: VariableTracker,
        rest: Sequence[VariableTracker],
        tree_map_kwargs: dict[str, VariableTracker],
        keypath: tuple[Any, ...],
    ) -> VariableTracker:
        other_dicts: list[ConstDictVariable] = []
        for candidate in rest:
            candidate = candidate.realize()
            if not isinstance(candidate, ConstDictVariable) or len(
                candidate.items
            ) != len(self.items):
                return self._tree_map_with_path_fallback(
                    tx, tree_map_fn, map_fn, rest, tree_map_kwargs, keypath
                )
            other_dicts.append(candidate)

        new_items_hashed = type(self.items)()
        for key_tracker, value in self.items.items():
            sibling_leaves: list[VariableTracker] = []
            for candidate in other_dicts:
                try:
                    sibling_leaves.append(candidate.items[key_tracker])
                except KeyError:
                    return self._tree_map_with_path_fallback(
                        tx, tree_map_fn, map_fn, rest, tree_map_kwargs, keypath
                    )
            key_const = key_tracker.vt.as_python_constant()
            child_keypath = keypath + (MappingKey(key_const),)
            new_items_hashed[key_tracker] = value.call_tree_map_with_path(
                tx,
                tree_map_fn,
                map_fn,
                sibling_leaves,
                tree_map_kwargs,
                child_keypath,
            )

        updated_original_items = {
            key_tracker.vt: new_items_hashed[key_tracker]
            for key_tracker in new_items_hashed
        }

        return self.clone(
            items=new_items_hashed,
            original_items=updated_original_items,
            should_reconstruct_all=True,
            source=None,
            mutation_type=ValueMutationNew(),
        )