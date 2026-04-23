def checkTrace(self, func, reference_tensors, input_tensors=None,
                   drop=None, allow_unused=False, verbose=False,
                   inputs_require_grads=True, check_tolerance=1e-5, export_import=True,
                   _force_outplace=False, grad_atol=None, grad_rtol=None):

        # TODO: check gradients for parameters, not just inputs
        def allSum(vs):
            # drop allows us to remove some values from ever being used
            # to test unused outputs
            if drop is not None:
                vs = vs[:-drop]
            # we don't want all the grad for all the outputs to be the same
            # so we multiply each by a constant
            return sum(math.log(i + 2) * v.sum() for i, v in enumerate(vs) if v is not None)
        if input_tensors is None:
            input_tensors = reference_tensors

        def flatten_inputs(inputs):
            def input_reduce(input, fn, acc):
                if isinstance(input, torch.Tensor):
                    fn(input, acc)
                elif isinstance(input, dict):
                    reduce(lambda acc, key: input_reduce(input[key], fn, acc), input, acc)
                else:
                    reduce(lambda acc, val: input_reduce(val, fn, acc), input, acc)
                return acc
            return tuple(input_reduce(recording_inputs, lambda t, acc: acc.append(t), []))

        nograd_inputs = reference_tensors
        if inputs_require_grads:
            recording_inputs = do_input_map(lambda t: t.clone().requires_grad_(), reference_tensors)
            flattened_recording_inputs = flatten_inputs(recording_inputs)
        else:
            recording_inputs = reference_tensors

        # `check_trace` is set to False because check_trace is run with @no_grad
        # Also, `checkTrace` already does all the checks
        # against python function
        ge = torch.jit.trace(func, input_tensors, check_tolerance=check_tolerance,
                             _force_outplace=_force_outplace, check_trace=False)

        if export_import:
            ge = self.getExportImportCopy(ge)

        if verbose:
            print(ge.graph)

        # test no gradients case
        outputs = func(*nograd_inputs)
        outputs_ge = ge(*nograd_inputs)
        self.assertEqual(outputs, outputs_ge)

        # test gradients case
        outputs = func(*recording_inputs)
        if inputs_require_grads:
            grads = torch.autograd.grad(allSum(outputs), flattened_recording_inputs,
                                        allow_unused=allow_unused)

        outputs_ge = ge(*recording_inputs)
        if inputs_require_grads:
            grads_ge = torch.autograd.grad(allSum(outputs_ge), flattened_recording_inputs,
                                           allow_unused=allow_unused)
        self.assertEqual(outputs, outputs_ge)
        if inputs_require_grads:
            self.assertEqual(grads, grads_ge, atol=grad_atol, rtol=grad_rtol)

        # test the grad grad case
        outputs = func(*recording_inputs)
        l1 = allSum(outputs)
        if inputs_require_grads:
            grads = torch.autograd.grad(l1, flattened_recording_inputs, create_graph=True,
                                        allow_unused=allow_unused)
        if inputs_require_grads:
            l2 = (allSum(grads) * l1)
            grads2 = torch.autograd.grad(l2, flattened_recording_inputs, allow_unused=allow_unused)

        if inputs_require_grads:
            recording_inputs = do_input_map(lambda t: Variable(t, requires_grad=True), reference_tensors)
            flattened_recording_inputs = flatten_inputs(recording_inputs)

        outputs_ge = ge(*recording_inputs)
        l1_ge = allSum(outputs_ge)
        if inputs_require_grads:
            grads_ge = torch.autograd.grad(
                l1_ge, flattened_recording_inputs, create_graph=True, allow_unused=allow_unused)

        if inputs_require_grads:
            l2_ge = (allSum(grads_ge) * l1_ge)
            grads2_ge = torch.autograd.grad(l2_ge, flattened_recording_inputs, allow_unused=allow_unused)

        self.assertEqual(outputs, outputs_ge)
        if inputs_require_grads:
            self.assertEqual(grads, grads_ge, atol=grad_atol, rtol=grad_rtol)
            for g2, g2_ge in zip(grads2, grads2_ge, strict=True):
                if g2 is None and g2_ge is None:
                    continue
                self.assertEqual(g2, g2_ge, atol=8e-4, rtol=8e-4)

        return ge