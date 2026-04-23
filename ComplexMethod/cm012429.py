def codegen_conditions(
        self,
        code: BracesBuffer,
        prefix: str | None = None,
        var: sympy.Symbol | None = None,
    ):
        if prefix is None:
            prefix = ""
        if not self.active_ranges:
            return True
        conditions = []

        def gen(start, end, var):
            if start == end:
                return False
            var_id = None
            for i, _var in enumerate(self.itervars):
                if var == _var:
                    var_id = i
                    break
            if (
                type(self) is CppKernel
                and var_id
                and start == 0
                and end == self.ranges[var_id]
            ):
                end = 1
            # pyrefly: ignore [bad-argument-type]
            conditions.append(f"{var} >= {cexpr_index(start)}")
            # pyrefly: ignore [bad-argument-type]
            conditions.append(f"{var} < {cexpr_index(end)}")
            return True

        if var is not None:
            assert var in self.active_ranges
            start, end = self.active_ranges[var]
            if not gen(start, end, var):
                return False
        else:
            for _var, _range in self.active_ranges.items():
                start, end = _range
                if not gen(start, end, _var):
                    return False
        joined_conditions = " && ".join(conditions)
        if joined_conditions:
            code.writeline(f"if({prefix}({joined_conditions}))")
            return True
        else:
            return False