def relabeled_clone(self, change_map):
        clone = self.clone()
        clone.change_aliases(change_map)
        return clone