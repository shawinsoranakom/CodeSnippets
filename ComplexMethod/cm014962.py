def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs or {}
        self.test_case.precision = self.precision
        self.test_case.rel_tol = self.rel_tol

        test_expect = self._get_expected_test_result(func)

        expected = run_meta_crossref(
            self.test_case,
            test_expect,
            func,
            args,
            kwargs,
            dtype=self.dtype,
            device_type=self.device_type,
            run_symbolic_meta=self.symbolic_meta,
        )

        # This is to test torch ops that do not have an out parameter but have
        # aten op overloads that have out parameters. Additionally, Python decompositions
        # may register OpOverloadPacket's so decompositions need to be tested
        # to ensure all OpOverloads still function for the Meta key (e.g. if a python decomposition
        # is registered for an aten op aten.foo with overloads [default, out], the python
        # function needs to support receiving `out` arguments)
        if (
            not self.inplace and
            not self.supports_out and
            test_expect == TestExpect.SUCCESS and
            (torch.is_tensor(expected) or isinstance(expected, Iterable))
        ):

            # check to see if there is a potential out overload
            num_outputs = 1 if torch.is_tensor(expected) else len(expected)
            func_out_overload, out_param_names, kwargs = self.try_resolve_aten_out_overload(func, args, kwargs, num_outputs)

            if func_out_overload:

                if num_outputs == 1:
                    kwargs[out_param_names[0]] = expected
                else:
                    for ind, out_param_name in enumerate(out_param_names):
                        kwargs[out_param_name] = expected[ind]

                test_expect = self._get_expected_test_result(func_out_overload)

                run_meta_crossref(
                    self.test_case,
                    test_expect,
                    func_out_overload,
                    args,
                    kwargs,
                    dtype=self.dtype,
                    device_type=self.device_type,
                    run_symbolic_meta=self.symbolic_meta,
                )

        return expected