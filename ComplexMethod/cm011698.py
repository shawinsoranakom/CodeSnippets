def used_or_aliased_buffer_names(self) -> OrderedSet[str]:
        """
        Returns buffer names used by this node, including aliases.

        Note: is_fake WeakDeps are excluded since they are purely for ordering
        and should not affect buffer lifetime.
        """
        used_names: OrderedSet[str] = OrderedSet()

        deps = [
            dep.name
            for dep in itertools.chain(self.read_writes.reads, self.read_writes.writes)
            if not (isinstance(dep, WeakDep) and dep.is_fake)
        ]
        while len(deps) > 0:
            dep = deps.pop()
            used_names.add(dep)
            if V.graph.name_to_buffer.get(dep):
                deps.extend(
                    alias
                    for alias in V.graph.name_to_buffer[
                        dep
                    ].get_inputs_that_alias_output()
                    if alias not in used_names
                )
        return used_names