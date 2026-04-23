def match(self, other):
        if not other:
            return False

        if not isinstance(other, MediaType):
            other = MediaType(other)

        main_types = [self.main_type, other.main_type]
        sub_types = [self.sub_type, other.sub_type]

        # Main types and sub types must be defined.
        if not all((*main_types, *sub_types)):
            return False

        # Main types must match or one be "*", same for sub types.
        for this_type, other_type in (main_types, sub_types):
            if this_type != other_type and this_type != "*" and other_type != "*":
                return False

        if bool(self.range_params) == bool(other.range_params):
            # If both have params or neither have params, they must be
            # identical.
            result = self.range_params == other.range_params
        else:
            # If self has params and other does not, it's a match.
            # If other has params and self does not, don't match.
            result = bool(self.range_params or not other.range_params)
        return result