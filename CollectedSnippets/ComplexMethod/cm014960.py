def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs or {}

        if (
            torch.jit.is_tracing() or isinstance(func, torch.ScriptMethod) or
            # meta converter doesn't work correctly when no_dispatch() is on, so
            # skip running the crossref test in this case
            torch._C._dispatch_tls_local_exclude_set().has(torch._C.DispatchKey.Python)
        ):
            return func(*args, **kwargs)

        if self.dtype in meta_function_skips.get(func, set()):
            test_expect = TestExpect.SKIP
        elif self.dtype in meta_function_device_skips[self.device_type].get(func, set()):
            test_expect = TestExpect.SKIP
        elif self.dtype in meta_function_expected_failures.get(func, set()):
            test_expect = TestExpect.XFAILURE
        elif self.dtype in meta_function_device_expected_failures[self.device_type].get(func, set()):
            test_expect = TestExpect.XFAILURE
        elif meta_function_expected_failures_conditional.get(func, lambda *_, **__: False)(self.dtype, *args, **kwargs):
            test_expect = TestExpect.XFAILURE
        elif not self.inplace and \
                self.dtype in meta_function_device_expected_failures_only_outplace[self.device_type].get(func, set()):
            test_expect = TestExpect.XFAILURE
        else:
            test_expect = TestExpect.SUCCESS

        return run_meta_crossref(
            self.test_case, test_expect, func, args,
            kwargs, dtype=self.dtype, device_type=self.device_type, run_symbolic_meta=False
        )