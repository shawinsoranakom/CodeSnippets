def promote(self):
        new = self.relabeled_clone({})
        new.join_type = LOUTER
        return new