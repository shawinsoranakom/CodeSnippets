def __call__(self, f):
        def wrapper():
            return f() and self.myattr

        return update_wrapper(wrapper, f)