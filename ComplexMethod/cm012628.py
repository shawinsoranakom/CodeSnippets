def has_non_contiguous_pw_in_reduction_kernel(self) -> bool:
        pointwise_nodes = [
            n
            for n in self.scheduler_nodes()
            if not n.is_reduction()
            and n.group[1][0] == self.numel * self.reduction_numel
        ]
        for node in pointwise_nodes:
            # An index can be an integer when loading a random seed.
            if not all(
                not isinstance(dep, MemoryDep)
                or dep.is_contiguous()
                or isinstance(dep.index, (sympy.Integer, int))
                or dep.stride1_for_last_dim()
                for dep in itertools.chain(
                    node.read_writes.reads, node.read_writes.writes
                )
            ):
                return True
        return False