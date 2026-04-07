def __str__(self):
        return '<%s: %s> tagged "%s"' % (
            self.tagged.__class__.__name__,
            self.tagged,
            self.name,
        )