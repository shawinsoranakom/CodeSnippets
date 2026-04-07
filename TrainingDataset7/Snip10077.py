def deep_deconstruct(self, obj):
        """
        Recursive deconstruction for a field and its arguments.
        Used for full comparison for rename/alter; sometimes a single-level
        deconstruction will not compare correctly.
        """
        if isinstance(obj, list):
            return [self.deep_deconstruct(value) for value in obj]
        elif isinstance(obj, tuple):
            return tuple(self.deep_deconstruct(value) for value in obj)
        elif isinstance(obj, dict):
            return {key: self.deep_deconstruct(value) for key, value in obj.items()}
        elif isinstance(obj, functools.partial):
            return (
                obj.func,
                self.deep_deconstruct(obj.args),
                self.deep_deconstruct(obj.keywords),
            )
        elif isinstance(obj, COMPILED_REGEX_TYPE):
            return RegexObject(obj)
        elif isinstance(obj, type):
            # If this is a type that implements 'deconstruct' as an instance
            # method, avoid treating this as being deconstructible itself - see
            # #22951
            return obj
        elif hasattr(obj, "deconstruct"):
            deconstructed = obj.deconstruct()
            if isinstance(obj, models.Field):
                # we have a field which also returns a name
                deconstructed = deconstructed[1:]
            path, args, kwargs = deconstructed
            return (
                path,
                [self.deep_deconstruct(value) for value in args],
                {key: self.deep_deconstruct(value) for key, value in kwargs.items()},
            )
        else:
            return obj