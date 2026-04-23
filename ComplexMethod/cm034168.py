def _extend_value(self, value, new_value, prepend=False):
        """
        Will extend the value given with new_value (and will turn both
        into lists if they are not so already). The values are run through
        a set to remove duplicate values.
        """

        if not isinstance(value, list):
            value = [value]
        if not isinstance(new_value, list):
            new_value = [new_value]

        # Due to where _extend_value may run for some attributes
        # it is possible to end up with Sentinel in the list of values
        # ensure we strip them
        value = [v for v in value if v is not Sentinel]
        new_value = [v for v in new_value if v is not Sentinel]

        if prepend:
            combined = new_value + value
        else:
            combined = value + new_value

        return [i for i, dummy in itertools.groupby(combined) if i is not None]