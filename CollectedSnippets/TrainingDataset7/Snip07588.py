def __repr__(self):
        extra_tags = f", extra_tags={self.extra_tags!r}" if self.extra_tags else ""
        return f"Message(level={self.level}, message={self.message!r}{extra_tags})"