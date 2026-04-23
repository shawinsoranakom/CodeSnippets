def can_inplace(self, read_dep: dependencies.Dep) -> bool:
        if self.is_template():
            return False
        if any(out.get_aliases() for out in self.get_outputs()):
            return False
        if len(self.read_writes.writes) == 1 and isinstance(
            read_dep, dependencies.MemoryDep
        ):
            write_dep = next(iter(self.read_writes.writes))
            assert isinstance(write_dep, dependencies.MemoryDep), f"{type(write_dep)=}"
            return read_dep.index == write_dep.index and read_dep.size == write_dep.size
        return False