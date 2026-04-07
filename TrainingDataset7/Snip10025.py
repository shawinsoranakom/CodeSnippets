def combine_expression(self, connector, sub_expressions):
        # SQLite doesn't have a ^ operator, so use the user-defined POWER
        # function that's registered in connect().
        if connector == "^":
            return "POWER(%s)" % ",".join(sub_expressions)
        elif connector == "#":
            return "BITXOR(%s)" % ",".join(sub_expressions)
        return super().combine_expression(connector, sub_expressions)