def tag_function(self, func):
        self.tags[func.__name__] = func
        return func