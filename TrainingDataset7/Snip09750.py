def combine_expression(self, connector, sub_expressions):
        lhs, rhs = sub_expressions
        if connector == "%%":
            return "MOD(%s)" % ",".join(sub_expressions)
        elif connector == "&":
            return "BITAND(%s)" % ",".join(sub_expressions)
        elif connector == "|":
            return "BITAND(-%(lhs)s-1,%(rhs)s)+%(lhs)s" % {"lhs": lhs, "rhs": rhs}
        elif connector == "<<":
            return "(%(lhs)s * POWER(2, %(rhs)s))" % {"lhs": lhs, "rhs": rhs}
        elif connector == ">>":
            return "FLOOR(%(lhs)s / POWER(2, %(rhs)s))" % {"lhs": lhs, "rhs": rhs}
        elif connector == "^":
            return "POWER(%s)" % ",".join(sub_expressions)
        elif connector == "#":
            raise NotSupportedError("Bitwise XOR is not supported in Oracle.")
        return super().combine_expression(connector, sub_expressions)