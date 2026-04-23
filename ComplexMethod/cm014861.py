def _test_make_fx_helper(self, device, dtype, op, tracing_mode, inplace=False, out=False):
    fn = _get_safe_inplace(op.get_inplace()) if inplace else op.op
    sample_inputs_itr = op.sample_inputs(device, dtype, requires_grad=False)

    # Limit ourselves to first 100 inputs so symbolic tracing tests don't take too long
    count = 100
    if out:
        count = 5
    for sample_input in itertools.islice(sample_inputs_itr, count):
        if inplace and sample_input.broadcasts_input:
            continue
        args = [sample_input.input] + list(sample_input.args)
        kwargs = sample_input.kwargs
        if out:
            expected = fn(*args, **kwargs)
            kwargs['out'] = expected

        try:
            optests.make_fx_check(fn, args, kwargs, tracing_mode, self.assertEqual,
                                  randomize_data=True)
        except DynamicOutputShapeException:
            self.skipTest("Dynamic output shape operation in trace")