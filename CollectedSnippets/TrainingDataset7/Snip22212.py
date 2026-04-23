def natural_key(self):
        return (self.name,) + self.author.natural_key()