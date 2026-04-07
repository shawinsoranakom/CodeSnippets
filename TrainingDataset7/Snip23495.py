def save(self, *args, **kwargs):
                self.instance.saved_by = "custom method"
                return super().save(*args, **kwargs)