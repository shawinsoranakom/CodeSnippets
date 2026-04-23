def test_lifetime_of_grad_fn_when_result_is_saved(self, device, dtype, op):
        def get_ref(func, sample):
            class Foo:
                pass

            out = func(
                (sample.input, *sample.args),
                is_cuda=False,
                expect_fastpath=False,
                **sample.kwargs,
            )
            foo = Foo()
            meta_dict = out[0].grad_fn.metadata
            meta_dict[0] = foo
            ref = weakref.ref(foo)
            return out, ref

        def _test(func, sample):
            out, ref = get_ref(func, sample)
            self.assertIsNotNone(ref())
            del out
            self.assertIsNone(ref())

        func = self._get_funcs(op)[0]
        for sample in op.sample_inputs(
            device, dtype, requires_grad=True, num_input_tensors=[1]
        ):
            for key in ("is_fastpath", "disable_fastpath"):
                if key in sample.kwargs:
                    del sample.kwargs[key]
            # note: `_foreach_pow.Scalar` and `_foreach_pow.ScalarList` don't depend on `result`
            # see: https://github.com/pytorch/pytorch/blob/5403c777/tools/autograd/derivatives.yaml#L3048-L3049
            if op.name == "_foreach_pow":
                if (
                    isinstance(sample.args[0], list)
                    and isinstance(sample.args[0][0], Number)
                ) or (
                    isinstance(sample.args[0], Number)
                    and not isinstance(sample.args[0], float)
                ):
                    continue
                if isinstance(sample.args[0], float):
                    new_args = (sample.input,)
                    sample.input = sample.args[0]
                    sample.args = new_args
            _test(func, sample)