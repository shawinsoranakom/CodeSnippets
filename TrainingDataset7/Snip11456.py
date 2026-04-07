def formfield(self, **kwargs):
        if self.remote_field.parent_link:
            return None
        return super().formfield(**kwargs)