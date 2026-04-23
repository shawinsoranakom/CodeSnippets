def save(self, *args, force_insert=False, force_update=False, **kwargs):
        super().save(
            *args, force_insert=force_insert, force_update=force_update, **kwargs
        )
        if not self.base:
            self.base = self
            super().save(*args, **kwargs)