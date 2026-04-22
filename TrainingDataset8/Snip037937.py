def pretty_print(self):
        def to_str(v):
            try:
                return "Object of type %s: %s" % (type_util.get_fqn_type(v), str(v))
            except Exception:
                return "<Unable to convert item to string>"

        # IDEA: Maybe we should remove our internal "hash_funcs" from the
        # stack. I'm not removing those now because even though those aren't
        # useful to users I think they might be useful when we're debugging an
        # issue sent by a user. So let's wait a few months and see if they're
        # indeed useful...
        return "\n".join(to_str(x) for x in reversed(self._stack.values()))