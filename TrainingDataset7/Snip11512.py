def field(self):
        """
        Add compatibility with the fetcher protocol. While self.related is not
        a field but a OneToOneRel, it quacks enough like a field to work.
        """
        return self.related