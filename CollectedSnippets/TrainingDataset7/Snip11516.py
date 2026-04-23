def __reduce__(self):
        # Same purpose as ForwardManyToOneDescriptor.__reduce__().
        return getattr, (self.related.model, self.related.name)