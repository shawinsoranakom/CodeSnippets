def clone(self):
        obj = super().clone()
        obj.related_updates = self.related_updates.copy()
        return obj