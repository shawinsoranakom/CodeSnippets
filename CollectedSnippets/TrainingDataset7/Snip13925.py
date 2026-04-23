def __get__(self, instance, cls=None):
        # Trigger access for all bases.
        if any(getattr(base, "__unittest_skip__", False) for base in cls.__bases__):
            return True
        for condition, reason in self.conditions:
            if condition():
                # Override this descriptor's value and set the skip reason.
                cls.__unittest_skip__ = True
                cls.__unittest_skip_why__ = reason
                return True
        return False