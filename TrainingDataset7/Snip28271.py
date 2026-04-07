def save(self, force_insert=False, force_update=False):
        super().save(force_insert=force_insert, force_update=force_update)
        self._savecount += 1