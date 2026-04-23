def stride1_for_last_dim(self, result_for_complex_expression: bool = True) -> bool:
        """
        Whether the stride for the last dimension is 1.
        """
        # python test/inductor/test_torchinductor_opinfo.py -k test_comprehensive_masked_scatter_cuda_float16
        # will exercise thru this corner case.
        if len(self.var_names) == 0:
            return True

        terms = self.index.args if isinstance(self.index, sympy.Add) else [self.index]

        last_sym = self.var_names[-1]
        for term in terms:
            if term == last_sym:
                return True

            # Having a >1 stride for the last dimension is bad for perf
            # return False.
            if (
                isinstance(term, sympy.Mul)
                and len(term.args) == 2
                and term.args[1] == last_sym
                and isinstance(term.args[0], (int, sympy.Integer))
                and term.args[0] > 1
            ):
                return False

        return result_for_complex_expression