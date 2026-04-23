def __get__(self, instance, owner):
                if instance is None:
                    raise AttributeError()