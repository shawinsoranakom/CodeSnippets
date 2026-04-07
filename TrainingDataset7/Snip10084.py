def _sort_migrations(self):
        """
        Reorder to make things possible. Reordering may be needed so FKs work
        nicely inside the same app.
        """
        for app_label, ops in sorted(self.generated_operations.items()):
            ts = TopologicalSorter()
            for op in ops:
                ts.add(op)
                for dep in op._auto_deps:
                    # Resolve intra-app dependencies to handle circular
                    # references involving a swappable model.
                    dep = self._resolve_dependency(dep)[0]
                    if dep.app_label != app_label:
                        continue
                    ts.add(op, *(x for x in ops if self.check_dependency(x, dep)))
            self.generated_operations[app_label] = list(ts.static_order())