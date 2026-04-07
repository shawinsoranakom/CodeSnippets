def lookup_str(self):
        """
        A string that identifies the view (e.g. 'path.to.view_function' or
        'path.to.ClassBasedView').
        """
        callback = self.callback
        if isinstance(callback, functools.partial):
            callback = callback.func
        if hasattr(callback, "view_class"):
            callback = callback.view_class
        elif not hasattr(callback, "__name__"):
            return callback.__module__ + "." + callback.__class__.__name__
        return callback.__module__ + "." + callback.__qualname__