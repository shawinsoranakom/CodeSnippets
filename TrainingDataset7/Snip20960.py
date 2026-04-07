def __get__(self, instance, cls=None):
                return bound_wrapper(self.wrapped.__get__(instance, cls))