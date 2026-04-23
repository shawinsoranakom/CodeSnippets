def _should_disable_fastpath(self, opinfo, rightmost_arg, rightmost_arg_type, dtype):
        if self.arity == 1:
            if "foreach_abs" in opinfo.name and dtype in complex_types():
                return True
            if "foreach_clone" in opinfo.name:
                return False
            # unary
            if opinfo.ref in (torch.abs, torch.neg):
                return False
            if opinfo.ref_inplace == torch.Tensor.zero_:
                return False
            return dtype in integral_types_and(torch.bool)
        if self.arity < 2 or rightmost_arg_type == ForeachRightmostArgType.Tensor:
            return None
        if "foreach_pow" in opinfo.name and dtype in integral_types_and(torch.bool):
            return True
        if any(
                foreach_name in opinfo.name
                for foreach_name in ("foreach_clamp_max", "foreach_clamp_min", "foreach_maximum", "foreach_minimum")
        ) and dtype in integral_types_and(torch.bool):
            return True
        if rightmost_arg_type == ForeachRightmostArgType.TensorList:
            disable_fastpath = "foreach_div" in opinfo.name and dtype in integral_types_and(torch.bool)
            if "foreach_add" in opinfo.name and dtype == torch.bool:
                disable_fastpath = True
            return disable_fastpath
        elif rightmost_arg_type == ForeachRightmostArgType.Scalar:
            disable_fastpath = "foreach_div" in opinfo.name and dtype in integral_types_and(torch.bool)
            if isinstance(rightmost_arg, bool):
                disable_fastpath |= dtype == torch.bool
                if opinfo.ref in (torch.add, torch.mul):
                    disable_fastpath = False
            elif isinstance(rightmost_arg, int):
                disable_fastpath |= dtype == torch.bool
            elif isinstance(rightmost_arg, float):
                disable_fastpath |= dtype in integral_types_and(torch.bool)
            elif isinstance(rightmost_arg, complex):
                disable_fastpath |= dtype not in complex_types()
            else:
                raise AssertionError(f"Invalid scalar of type {rightmost_arg_type} - {rightmost_arg}")
            return disable_fastpath
        elif rightmost_arg_type == ForeachRightmostArgType.ScalarList:
            disable_fastpath = opinfo.ref == torch.div and dtype in integral_types_and(torch.bool)
            elmt_t = type(rightmost_arg[0])
            has_same_type = all(isinstance(v, elmt_t) for v in rightmost_arg)
            if not has_same_type:
                return dtype not in complex_types()
            if isinstance(rightmost_arg[0], bool):
                if ("foreach_add" in opinfo.name or "foreach_mul" in opinfo.name) and dtype == torch.bool:
                    disable_fastpath = False
            elif isinstance(rightmost_arg[0], int):
                disable_fastpath |= dtype == torch.bool
            elif isinstance(rightmost_arg[0], float):
                disable_fastpath |= dtype in integral_types_and(torch.bool)
            elif isinstance(rightmost_arg[0], complex):
                disable_fastpath |= dtype not in complex_types()
            else:
                raise AssertionError(f"Invalid scalarlist of {rightmost_arg}")
            return disable_fastpath
        else:
            raise AssertionError(f"Invalid rightmost_arg_type of {rightmost_arg_type}")