def fusable_read_and_write(self, read: Dep, write: MemoryDep) -> bool:
        if isinstance(read, MemoryDep):
            read_name = self.mutation_renames.get(read.name, read.name)

            if (
                read_name != write.name
                or free_symbol_is_type(read.index, SymT.TMP)
                or free_symbol_is_type(write.index, SymT.TMP)
            ):
                return False

            if config.loop_ordering_after_fusion and read.num_vars != write.num_vars:
                # Need merge loops if we do loop ordering after fusion since
                # we have not merged the loops yet when creating the scheduler
                # nodes.
                read = read.normalize()
                write = write.normalize()
            # Operations like index_add_, scatter_add_, etc. require global
            # synchronization - all threads must complete writes before any reads.
            # These cannot be safely fused into the same kernel. Atomic modes and TMA stores require synchronization barriers
            if self.mode_requires_synchronization(write.mode):
                return False

            return (
                read.index == write.index
                and len(read.size) >= len(write.size)
                and read.size[: len(write.size)] == write.size
            )
        elif isinstance(read, StarDep):
            read_name = self.mutation_renames.get(read.name, read.name)
            write_name = self.mutation_renames.get(write.name, write.name)
            if (
                read.mode == write.mode
                and write.mode is not None
                and read_name == write_name
            ):
                return True
        return False