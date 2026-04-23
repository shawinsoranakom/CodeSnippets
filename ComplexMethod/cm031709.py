def deprecate_positional_use(
        self,
        func: Function,
        params: dict[int, Parameter],
    ) -> str:
        assert len(params) > 0
        first_pos = next(iter(params))
        last_pos = next(reversed(params))

        # Format the deprecation message.
        if len(params) == 1:
            condition = f"nargs == {first_pos+1}"
            amount = f"{first_pos+1} " if first_pos else ""
            pl = "s"
        else:
            condition = f"nargs > {first_pos} && nargs <= {last_pos+1}"
            amount = f"more than {first_pos} " if first_pos else ""
            pl = "s" if first_pos != 1 else ""
        message = (
            f"Passing {amount}positional argument{pl} to "
            f"{func.fulldisplayname}() is deprecated."
        )

        for (major, minor), group in itertools.groupby(
            params.values(), key=attrgetter("deprecated_positional")
        ):
            names = [repr(p.name) for p in group]
            pstr = libclinic.pprint_words(names)
            if len(names) == 1:
                message += (
                    f" Parameter {pstr} will become a keyword-only parameter "
                    f"in Python {major}.{minor}."
                )
            else:
                message += (
                    f" Parameters {pstr} will become keyword-only parameters "
                    f"in Python {major}.{minor}."
                )

        # Append deprecation warning to docstring.
        docstring = textwrap.fill(f"Note: {message}")
        func.docstring += f"\n\n{docstring}\n"
        # Format and return the code block.
        code = self.DEPRECATION_WARNING_PROTOTYPE.format(
            condition=condition,
            errcheck="",
            message=libclinic.wrapped_c_string_literal(message, width=64,
                                                       subsequent_indent=20),
        )
        return libclinic.normalize_snippet(code, indent=4)