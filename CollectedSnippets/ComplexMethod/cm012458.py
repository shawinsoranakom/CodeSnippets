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