def assertInHTML(self, needle, haystack, count=None, msg_prefix=""):
        parsed_needle = assert_and_parse_html(
            self, needle, None, "First argument is not valid HTML:"
        )
        parsed_haystack = assert_and_parse_html(
            self, haystack, None, "Second argument is not valid HTML:"
        )
        real_count = parsed_haystack.count(parsed_needle)

        if (count is None and real_count > 0) or count == real_count:
            return

        if msg_prefix:
            msg_prefix += ": "
        haystack_repr = safe_repr(haystack)
        if count is not None:
            if count == 0:
                msg = (
                    f"{needle!r} unexpectedly found in the following response\n"
                    f"{haystack_repr}"
                )
            else:
                msg = (
                    f"Found {real_count} instances of {needle!r} (expected {count}) in "
                    f"the following response\n{haystack_repr}"
                )
            msg = f"{real_count} != {count} : {msg_prefix}{msg}"
        else:
            msg = (
                f"False is not true : {msg_prefix}Couldn't find {needle!r} in the "
                f"following response\n{haystack_repr}"
            )
        self.fail(msg)