def demote(self):
        new = self.relabeled_clone({})
        new.join_type = INNER
        return new