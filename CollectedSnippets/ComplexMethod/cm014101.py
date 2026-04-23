def call_tree_map_branch(
        self,
        tx: "InstructionTranslator",
        tree_map_fn: UserFunctionVariable,
        map_fn: VariableTracker,
        rest: Sequence[VariableTracker],
        tree_map_kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if not isinstance(self, (ListVariable, TupleVariable)):
            return self._tree_map_fallback(
                tx, tree_map_fn, map_fn, rest, tree_map_kwargs
            )

        other_lists: list[BaseListVariable] = []
        for candidate in rest:
            if (
                not isinstance(candidate, BaseListVariable)
                or len(candidate.items) != len(self.items)
                or self.python_type() != candidate.python_type()
            ):
                return self._tree_map_fallback(
                    tx, tree_map_fn, map_fn, rest, tree_map_kwargs
                )
            other_lists.append(candidate)

        new_items: list[VariableTracker] = []
        for idx, item in enumerate(self.items):
            sibling_leaves = [candidate.items[idx] for candidate in other_lists]
            new_items.append(
                item.call_tree_map(
                    tx,
                    tree_map_fn,
                    map_fn,
                    sibling_leaves,
                    tree_map_kwargs,
                )
            )

        return self.clone(
            items=new_items,
            source=None,
            mutation_type=ValueMutationNew(),
        )