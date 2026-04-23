def is_file(thing):
        return hasattr(thing, "read") and callable(thing.read)