def transfer_erased_node_deps(
        self, erased_to_new: dict[fx.Node, fx.Node | None]
    ) -> None:
        """
        Transfer all extra dependencies from erased nodes to their replacements, handling
        cross-dependencies between erased nodes correctly.

        Skips deps where both endpoints resolve to replacement nodes from the
        same erasure batch — these are intra-bucket deps that would create
        cycles (e.g. new_start <-> new_wait within the same bucket).
        """
        erased_merge_sets: dict[fx.Node, fx.Node | None] = {}

        for replaced, new in erased_to_new.items():
            for equiv in self.merge_sets[replaced]:
                erased_merge_sets[equiv] = new

        # Transfer dependencies
        for old_node, new_node in erased_merge_sets.items():
            if new_node is None:
                # Clean up references to removed node
                for extra_use in list(self.extra_uses[old_node]):
                    updated_use = erased_merge_sets.get(extra_use, extra_use)
                    if updated_use is not None:
                        self.extra_deps[updated_use].discard(old_node)
                for extra_dep in list(self.extra_deps[old_node]):
                    updated_dep = erased_merge_sets.get(extra_dep, extra_dep)
                    if updated_dep is not None:
                        self.extra_uses[updated_dep].discard(old_node)
            else:
                # Transfer dependencies FROM old_node (what old_node depended on)
                for extra_dep in self.extra_deps[old_node]:
                    updated_dep = erased_merge_sets.get(extra_dep, extra_dep)
                    if updated_dep is not None and updated_dep != new_node:
                        # Skip if reverse dep already exists (extra or data)
                        if new_node in self.extra_deps.get(
                            updated_dep, ()
                        ) or new_node in OrderedSet(updated_dep.all_input_nodes):
                            continue
                        self.extra_deps[new_node].add(updated_dep)
                        self.extra_uses[updated_dep].discard(old_node)
                        self.extra_uses[updated_dep].add(new_node)

                # Transfer dependencies TO old_node (what depended on old_node)
                for extra_use in self.extra_uses[old_node]:
                    updated_use = erased_merge_sets.get(extra_use, extra_use)
                    if updated_use is not None and updated_use != new_node:
                        # Skip if reverse dep already exists (extra or data)
                        if updated_use in self.extra_deps.get(
                            new_node, ()
                        ) or updated_use in OrderedSet(new_node.all_input_nodes):
                            continue
                        self.extra_deps[updated_use].discard(old_node)
                        self.extra_deps[updated_use].add(new_node)
                        self.extra_uses[new_node].add(updated_use)

        # Clean up erased nodes
        for old_node in erased_merge_sets:
            self.extra_deps[old_node].clear()
            self.extra_uses[old_node].clear()
            del self.merge_sets[old_node]