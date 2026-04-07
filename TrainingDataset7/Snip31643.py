def save(self, *args, **kwargs):
        """
        A save method that modifies the data in the object.
        A user-defined save() method isn't called when objects are deserialized
        (#4459).
        """
        self.data = 666
        super().save(*args, **kwargs)