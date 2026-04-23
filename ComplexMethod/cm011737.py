def can_fuse_vertical(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> bool:
        """
        Check if it is legal to fuse a consumer (node2) into a producer (node1).

        We can fuse them if all the reads of node2 either match
        corresponding writes in node1, or are written by nodes that can
        be scheduled before the fusion of node1 and node2.
        """
        node1_buf_names = node1.get_buffer_names()
        why = WhyNoFuse(node1, node2)
        remaining_deps_by_name: dict[str, list[Dep]] = defaultdict(list)

        for dep in node2.unmet_dependencies:
            name = self.mutation_renames.get(dep.name, dep.name)
            if isinstance(dep, WeakDep) and self.fusable_weak_dep(dep, node1, node2):
                continue
            remaining_deps_by_name[name].append(dep)

        for cd in node1.read_writes.writes:
            if not isinstance(cd, MemoryDep) and not isinstance(cd, StarDep):
                continue
            remaining = remaining_deps_by_name.get(
                self.mutation_renames.get(cd.name, cd.name)
            )
            if remaining:
                for rd in remaining:
                    if isinstance(cd, MemoryDep) and self.fusable_read_and_write(
                        rd, cd
                    ):
                        remaining.remove(rd)  # noqa: B909
                    elif isinstance(
                        cd, StarDep
                    ) and self.fusable_stardep_write_and_read_on_empty_tensor(
                        rd, cd, node1.node
                    ):
                        remaining.remove(rd)  # noqa: B909

        remaining_deps = OrderedSet(
            dep.name
            for dep in itertools.chain.from_iterable(remaining_deps_by_name.values())
        )

        if remaining_deps & node1_buf_names:
            # MemoryDeps didn't match and read different locations of the same buffer.
            # Examples here include:
            #   - MemoryDep("foo", x) != MemoryDep("foo", x + 1)
            #   - MemoryDep("foo", x) != StarDep("foo")
            why("memory deps did not match")
            return False

        node1_op_names = node1.get_operation_names()
        for name in remaining_deps:
            op_name = self.name_to_buf[name].defining_op_name()
            if node1_op_names & self.name_to_fused_node[op_name].ancestors:
                why("intermediate nodes between node1 & node2")
                return False

        return True