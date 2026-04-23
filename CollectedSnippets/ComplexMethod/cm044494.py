def _validate_type(self,  # pylint:disable=too-many-return-statements
                       expected_type: Any,
                       attr: Any,
                       depth=1) -> bool:
        """ Validate that provided types are correct when this Dataclass is initialized

        Parameters
        ----------
        expected_type : Any
            The expected data type for the given attribute
        attr : Any
            The attribute to test for correctness
        depth : int, optional
            The current recursion depth

        Returns
        -------
        bool
            ``True`` if the given attribute is a valid datatype

        Raises
        ------
        AssertionError
            On explicit data type failure
        ValueError
            On unhandled data type failure
        """
        value = getattr(self, attr)
        attr_type = type(value)
        expected_type = self.datatype if expected_type == T else expected_type  # type:ignore[misc]

        if attr_type is expected_type:
            return True

        if attr == "datatype":
            assert value in (str, bool, float, int, list), (
                "'datatype' must be one of str, bool, float, int or list. Got {value}")
            return True

        if expected_type == T:  # type:ignore[misc]
            assert attr_type == self.datatype, (
               f"'{attr}' expected: {self.datatype}. Got: {attr_type}")
            return True

        if get_origin(expected_type) is Literal:
            return value in get_args(expected_type)

        if get_origin(expected_type) in (Union, types.UnionType):
            for subtype in get_args(expected_type):
                if self._validate_type(subtype, attr, depth=depth + 1):
                    return True

        if get_origin(expected_type) in (list, tuple) and attr_type in (list, tuple):
            sub_expected = [self.datatype if v == T  # type:ignore[misc]
                            else v for v in get_args(expected_type)]
            return set(type(v) for v in value).issubset(sub_expected)

        if depth == 1:
            raise ValueError(f"'{attr}' expected: {expected_type}. Got: {attr_type}")

        return False