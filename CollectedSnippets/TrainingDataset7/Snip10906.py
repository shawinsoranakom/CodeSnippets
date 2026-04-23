def relabeled_clone(self, relabels):
        clone = self.copy()
        clone.source = self.source.relabeled_clone(relabels)
        return clone