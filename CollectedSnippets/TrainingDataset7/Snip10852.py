def __repr__(self):
        args = self.arg_joiner.join(str(arg) for arg in self.source_expressions)
        extra = {**self.extra, **self._get_repr_options()}
        if extra:
            extra = ", ".join(
                str(key) + "=" + str(val) for key, val in sorted(extra.items())
            )
            return "{}({}, {})".format(self.__class__.__name__, args, extra)
        return "{}({})".format(self.__class__.__name__, args)