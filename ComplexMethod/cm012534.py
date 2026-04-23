def can_fuse(self, node1, node2):  # type: ignore[override]
        if not super().can_fuse(node1, node2):
            return False
        # Pallas partial reductions use keepdims, so fusing two reductions
        # that read the same buffer with different index patterns produces
        # intermediates with incompatible shapes (e.g. (1,8) + (8,1) = (8,8)
        # instead of (8,)).  Prevent this by rejecting fusion when the read
        # indices differ.
        if node1.is_reduction() and node2.is_reduction():
            from torch._inductor.dependencies import MemoryDep

            reads1 = {}
            for dep in node1.read_writes.reads:
                if isinstance(dep, MemoryDep):
                    reads1[dep.name] = dep.index
            for dep in node2.read_writes.reads:
                if isinstance(dep, MemoryDep) and dep.name in reads1:
                    if reads1[dep.name] != dep.index:
                        return False
        return True