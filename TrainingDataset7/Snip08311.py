def dumps(self, obj):
        # For better incr() and decr() atomicity, don't pickle integers.
        # Using type() rather than isinstance() matches only integers and not
        # subclasses like bool.
        if type(obj) is int:
            return obj
        return pickle.dumps(obj, self.protocol)