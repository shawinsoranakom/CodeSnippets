def combine_expression(self, connector, sub_expressions):
        if connector == "^":
            return "POW(%s)" % ",".join(sub_expressions)
        # Convert the result to a signed integer since MySQL's binary operators
        # return an unsigned integer.
        elif connector in ("&", "|", "<<", "#"):
            connector = "^" if connector == "#" else connector
            return "CONVERT(%s, SIGNED)" % connector.join(sub_expressions)
        elif connector == ">>":
            lhs, rhs = sub_expressions
            return "FLOOR(%(lhs)s / POW(2, %(rhs)s))" % {"lhs": lhs, "rhs": rhs}
        return super().combine_expression(connector, sub_expressions)