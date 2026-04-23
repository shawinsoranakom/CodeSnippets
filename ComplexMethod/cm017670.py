def __init__(self, var):
        self.var = var
        self.literal = None
        self.lookups = None
        self.translate = False
        self.message_context = None

        if not isinstance(var, str):
            raise TypeError("Variable must be a string or number, got %s" % type(var))
        try:
            # First try to treat this variable as a number.
            #
            # Note that this could cause an OverflowError here that we're not
            # catching. Since this should only happen at compile time, that's
            # probably OK.

            # Try to interpret values containing a period or an 'e'/'E'
            # (possibly scientific notation) as a float;  otherwise, try int.
            if "." in var or "e" in var.lower():
                self.literal = float(var)
                # "2." is invalid
                if var[-1] == ".":
                    raise ValueError
            else:
                self.literal = int(var)
        except ValueError:
            # A ValueError means that the variable isn't a number.
            if var[0:2] == "_(" and var[-1] == ")":
                # The result of the lookup should be translated at rendering
                # time.
                self.translate = True
                var = var[2:-1]
            # If it's wrapped with quotes (single or double), then
            # we're also dealing with a literal.
            try:
                self.literal = mark_safe(unescape_string_literal(var))
            except ValueError:
                # Otherwise we'll set self.lookups so that resolve() knows
                # we're dealing with a bonafide variable
                if VARIABLE_ATTRIBUTE_SEPARATOR + "_" in var or var[0] == "_":
                    raise TemplateSyntaxError(
                        "Variables and attributes may "
                        "not begin with underscores: '%s'" % var
                    )
                # Disallow characters that are allowed in numbers but not in a
                # variable name.
                for c in ["+", "-"]:
                    if c in var:
                        raise TemplateSyntaxError(
                            "Invalid character ('%s') in variable name: '%s'" % (c, var)
                        )
                self.lookups = tuple(var.split(VARIABLE_ATTRIBUTE_SEPARATOR))