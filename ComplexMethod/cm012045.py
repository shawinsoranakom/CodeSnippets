def has_path(self, source: fx.Node, target: fx.Node) -> bool:
        """Check if there's a path from source to target."""
        # we should not be checking path from node to itself
        assert self.merge_sets[source] is not self.merge_sets[target]

        # search backwards from target to source
        visited: OrderedSet[fx.Node] = OrderedSet()
        queue = [target]
        visited.add(target)

        while queue:
            current = queue.pop()

            for dep in self.get_merged_deps(current):
                # Check if we reached source or its equivalent
                if dep in self.merge_sets[source]:
                    return True

                if dep in visited:
                    continue

                # We are searching from target, so this node is necessarily an ancestor
                # of target.
                # If dep is an ancestor of source, any path through dep to source would imply a cycle
                if self.node_ancestors:
                    source_set = self.merge_sets[source]
                    is_ancestor_of_source = any(
                        dep in self.node_ancestors[s] for s in source_set
                    )
                    # Add to visited to avoid recomputing this check if we see dep again
                    if is_ancestor_of_source:
                        visited.add(dep)
                        continue

                visited.add(dep)
                queue.append(dep)

        return False