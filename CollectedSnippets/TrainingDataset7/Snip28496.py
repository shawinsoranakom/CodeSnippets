def clean(self):
        # Ensure author is always accessible in clean method
        assert self.author.name is not None