def string_condition(self, a, b, operation, case_sensitive):
        if not case_sensitive:
            a = a.lower()
            b = b.lower()

        if operation == "a == b":
            return (a == b,)
        elif operation == "a != b":
            return (a != b,)
        elif operation == "a IN b":
            return (a in b,)
        elif operation == "a MATCH REGEX(b)":
            try:
                return (re.match(b, a) is not None,)
            except:
                return (False,)
        elif operation == "a BEGINSWITH b":
            return (a.startswith(b),)
        elif operation == "a ENDSWITH b":
            return (a.endswith(b),)