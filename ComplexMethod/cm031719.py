def parse_slash(self, function: Function, version: VersionTuple | None) -> None:
        """Parse positional-only parameter marker '/'.

        The 'version' parameter signifies the future version from which
        the marker will take effect (None means it is already in effect).
        """
        if not self.expecting_parameters:
            fail("Encountered '/' when not expecting parameters")

        if version is None:
            if self.deprecated_keyword:
                fail(f"Function {function.name!r}: '/' must precede '/ [from ...]'")
            if self.deprecated_positional:
                fail(f"Function {function.name!r}: '/' must precede '* [from ...]'")
            if self.keyword_only:
                fail(f"Function {function.name!r}: '/' must precede '*'")
            if self.positional_only:
                fail(f"Function {function.name!r} uses '/' more than once.")
        else:
            if self.deprecated_keyword:
                if self.deprecated_keyword == version:
                    fail(f"Function {function.name!r} uses '/ [from "
                         f"{version[0]}.{version[1]}]' more than once.")
                if self.deprecated_keyword > version:
                    fail(f"Function {function.name!r}: '/ [from "
                         f"{version[0]}.{version[1]}]' must precede '/ [from "
                         f"{self.deprecated_keyword[0]}.{self.deprecated_keyword[1]}]'")
            if self.deprecated_positional:
                fail(f"Function {function.name!r}: '/ [from ...]' must precede '* [from ...]'")
            if self.keyword_only:
                fail(f"Function {function.name!r}: '/ [from ...]' must precede '*'")
        self.positional_only = True
        self.deprecated_keyword = version
        if version is not None:
            found = False
            for p in reversed(function.parameters.values()):
                found = p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                break
            if not found:
                fail(f"Function {function.name!r} specifies '/ [from ...]' "
                     f"without preceding parameters.")
        # REQUIRED and OPTIONAL are allowed here, that allows positional-only
        # without option groups to work (and have default values!)
        allowed = {
            ParamState.REQUIRED,
            ParamState.OPTIONAL,
            ParamState.RIGHT_SQUARE_AFTER,
            ParamState.GROUP_BEFORE,
        }
        if (self.parameter_state not in allowed) or self.group:
            fail(f"Function {function.name!r} has an unsupported group configuration. "
                 f"(Unexpected state {self.parameter_state}.d)")
        # fixup preceding parameters
        for p in function.parameters.values():
            if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
                if version is None:
                    p.kind = inspect.Parameter.POSITIONAL_ONLY
                elif p.deprecated_keyword is None:
                    p.deprecated_keyword = version