def natural_key(self):
        return (self.codename, *self.content_type.natural_key())