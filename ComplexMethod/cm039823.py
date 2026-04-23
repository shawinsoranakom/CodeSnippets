def __exit__(self, exc_type, exc_value, _):
        # see
        # https://docs.python.org/2.5/whatsnew/pep-343.html#SECTION000910000000000000000

        if exc_type is None:  # No exception was raised in the block
            if self.may_pass:
                return True  # CM is happy
            else:
                err_msg = self.err_msg or f"Did not raise: {self.expected_exc_types}"
                raise AssertionError(err_msg)

        if not any(
            issubclass(exc_type, expected_type)
            for expected_type in self.expected_exc_types
        ):
            if self.err_msg is not None:
                raise AssertionError(self.err_msg) from exc_value
            else:
                return False  # will re-raise the original exception

        if self.matches is not None:
            err_msg = self.err_msg or (
                "The error message should contain one of the following "
                "patterns:\n{}\nGot {}".format("\n".join(self.matches), str(exc_value))
            )
            if not any(re.search(match, str(exc_value)) for match in self.matches):
                raise AssertionError(err_msg) from exc_value
            self.raised_and_matched = True

        return True