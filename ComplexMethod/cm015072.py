def __call__(self, inputs, is_cuda, expect_fastpath, **kwargs):
        actual = None
        zero_size = kwargs.pop("zero_size", False)

        # Skip profiler check for CUDA 12.6, 12.8 as the upgrade makes profiler results flaky
        # https://github.com/pytorch/pytorch/issues/148681. TODO: ADD IT BACK!!!
        skip_profiler_check = _get_torch_cuda_version() in [(12, 6), (12, 8)]
        if (
            is_cuda
            and not skip_profiler_check
            and torch.autograd.kineto_available()
            and torch.profiler.ProfilerActivity.CUDA
            in torch.profiler.supported_activities()
        ):
            with torch.profiler.profile() as p:
                actual = self.func(*inputs, **kwargs)
                # synchronize within the profiler context to make sure events happen before exiting
                torch.cuda.synchronize()
            keys = tuple([e.key for e in p.key_averages()])
            mta_called = any("multi_tensor_apply_kernel" in k for k in keys)

            if mta_called != (expect_fastpath and (not zero_size)):
                raise AssertionError(
                    f"{mta_called=}, {expect_fastpath=}, {zero_size=}, {self.func.__name__=}, {keys=}"
                )
        else:
            actual = self.func(*inputs, **kwargs)
        if self.is_inplace:
            if id(inputs[0]) != id(actual):
                raise AssertionError("expected inputs[0] is actual")
        return actual