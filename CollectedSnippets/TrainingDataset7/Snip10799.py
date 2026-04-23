def relabeled_clone(self, change_map):
        clone = self.copy()
        clone.set_source_expressions(
            [
                e.relabeled_clone(change_map) if e is not None else None
                for e in self.get_source_expressions()
            ]
        )
        return clone