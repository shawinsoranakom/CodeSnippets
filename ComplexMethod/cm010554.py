def _remove_dup_nodes(self):
        while True:
            to_delete = set()

            for idx in range(len(self)):
                if (
                    self[idx].cpu_parent is not None
                    and self[idx].cpu_parent.name == self[idx].name
                    and len(self[idx].cpu_parent.cpu_children) == 1
                ):
                    self[idx].cpu_parent.cpu_children = self[idx].cpu_children
                    self[idx].cpu_parent.kernels = self[idx].kernels  # lift kernels up
                    for ch in self[idx].cpu_children:
                        ch.cpu_parent = self[idx].cpu_parent
                    to_delete.add(idx)
            if len(to_delete) == 0:
                break

            new_evts = [ev for ind, ev in enumerate(self) if ind not in to_delete]

            self.clear()

            self.extend(new_evts)