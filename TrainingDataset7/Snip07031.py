def __eq__(self, other):
        """
        Do an equivalence test on the OGR type with the given
        other OGRGeomType, the short-hand string, or the integer.
        """
        if isinstance(other, OGRGeomType):
            return self.num == other.num
        elif isinstance(other, str):
            return self.name.lower() == other.lower()
        elif isinstance(other, int):
            return self.num == other
        else:
            return False