def fusable_weak_dep(
        self, weak_dep: WeakDep, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> bool:
        if weak_dep.name not in node1.get_buffer_names():
            return False

        # A weak dep can be fused if and only if the fused operation acts inplace
        # on the buffer being mutated. i.e. the same index is being read then mutated
        mutating_writes = [
            write
            for write in node2.read_writes.writes
            if write.name == weak_dep.mutating_buf
        ]
        if len(mutating_writes) != 1:
            return False
        write = mutating_writes[0]
        if isinstance(write, StarDep):
            return False
        assert isinstance(write, MemoryDep)

        if free_symbol_is_type(write.index, SymT.TMP):
            return False

        # Non-injective scatter: range vars absent from write index mean
        # multiple iterations hit the same location. Can't fuse the reader
        # in or it will see partially-written state between iterations.
        if not OrderedSet(write.var_names) <= write.index.free_symbols:
            return False

        real_name = self.mutation_real_name[weak_dep.mutating_buf]
        relevant_reading_nodes = [node1]
        if isinstance(node1, ForeachKernelSchedulerNode):
            relevant_reading_nodes = node1.snodes
        num_concurrent_reads = 0
        for reading_node in relevant_reading_nodes:
            relevant_reads = [
                read
                for read in reading_node.read_writes.reads
                if read.name == real_name
            ]
            if not relevant_reads:
                continue
            num_concurrent_reads += 1
            if not all(
                isinstance(read, MemoryDep)
                and not free_symbol_is_type(read.index, SymT.TMP)
                and read.index == write.index
                and read.size == write.size
                for read in relevant_reads
            ):
                return False
        return num_concurrent_reads <= 1