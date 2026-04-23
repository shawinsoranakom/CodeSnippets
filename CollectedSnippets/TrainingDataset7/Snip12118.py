def relabeled_clone(self, change_map):
        clone = self.clone()
        if resolved_condition := clone.resolved_condition:
            clone.resolved_condition = resolved_condition.relabeled_clone(change_map)
        return clone