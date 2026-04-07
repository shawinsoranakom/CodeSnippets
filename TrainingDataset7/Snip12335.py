def relabeled_clone(self, change_map):
        clone = self.clone()
        clone.relabel_aliases(change_map)
        return clone