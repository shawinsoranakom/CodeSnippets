def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.date.today()
        return super().save(*args, **kwargs)