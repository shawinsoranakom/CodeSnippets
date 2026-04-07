def dumps(self, obj):
        """
        The parameter is an already serialized list of Message objects. No need
        to serialize it again, only join the list together and encode it.
        """
        return ("[" + ",".join(obj) + "]").encode("latin-1")