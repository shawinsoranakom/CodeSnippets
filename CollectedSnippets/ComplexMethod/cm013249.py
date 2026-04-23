def _check_helper(self, device, dtype, op, variant, check, *, check_forward_ad=False, check_backward_ad=True,
                      check_batched_grad=None, check_batched_forward_grad=False):
        if check not in ('gradcheck', 'bwgrad_bwgrad', 'fwgrad_bwgrad'):
            raise AssertionError(
                f"check must be one of ('gradcheck', 'bwgrad_bwgrad', 'fwgrad_bwgrad'), got {check!r}"
            )
        # NB: check_backward_ad does not affect gradgradcheck (always True)
        if variant is None:
            self.skipTest("Skipped! Variant not implemented.")
        if not op.supports_dtype(dtype, torch.device(device).type):
            self.skipTest(f"Skipped! {op.name} does not support dtype {str(dtype)}")

        def is_inplace(variant):
            if hasattr(variant, "__wrapped__"):
                return variant.__wrapped__ is op.get_inplace()
            return variant is op.get_inplace()

        include_conjugated_inputs = op.test_conjugated_samples and dtype.is_complex

        samples = op.sample_inputs(device, dtype, requires_grad=True, include_conjugated_inputs=include_conjugated_inputs,
                                   small_inputs_only=TEST_WITH_SLOW_GRADCHECK)

        for sample in samples:
            if sample.broadcasts_input and is_inplace(variant):
                continue

            # Gradcheck expects tensors as its input, but autograd actually supports tensorlists
            #   and tensors passed as kwargs. The following creates a function that accepts just
            #   the tensors that require grad as varargs, and then recomposes them back into the
            #   original input.

            # Creates gradcheck inputs by identifying tensors requiring grad
            all_args = None
            if is_iterable_of_tensors(sample.input):
                all_args = chain(sample.input, sample.args, sample.kwargs.values())
            else:
                all_args = tuple(chain((sample.input,), sample.args, sample.kwargs.values()))  # type: ignore[assignment]
            gradcheck_args = tuple(x for x in all_args if (isinstance(x, torch.Tensor) and x.requires_grad))  # type: ignore[union-attr]

            # Verifies sample input tensors should have no grad
            # This may happen if the same tensor is used in two different SampleInputs
            for t in gradcheck_args:
                self.assertIsNone(t.grad,
                                  "A sampled input has a gradient before running autograd. "
                                  "This usually means that (at least) one input tensor is reused "
                                  "across different SampleInputs. "
                                  "Please create a new tensor for each SampleInput.")

            def _input_recomposition_helper(inputs, inp, input_idx):
                if is_iterable_of_tensors(inp):
                    tensor_list = []
                    for x in inp:
                        if isinstance(x, torch.Tensor) and x.requires_grad:
                            tensor_list.append(inputs[input_idx])
                            input_idx = input_idx + 1
                        else:
                            tensor_list.append(x)
                    return tensor_list, input_idx
                elif isinstance(inp, torch.Tensor) and inp.requires_grad:
                    return inputs[input_idx], input_idx + 1
                else:
                    return inp, input_idx

            def fn(*inputs):
                # Puts inputs back into sample properly
                positional_args = []
                input_idx = 0
                inp, input_idx = _input_recomposition_helper(inputs, sample.input, input_idx)
                positional_args.append(inp)

                for x in sample.args:
                    inp, input_idx = _input_recomposition_helper(inputs, x, input_idx)
                    positional_args.append(inp)

                # Recreates kwargs
                kwargs = {}
                for k, v in sample.kwargs.items():
                    inp, input_idx = _input_recomposition_helper(inputs, v, input_idx)
                    kwargs[k] = inp

                output = op.gradcheck_wrapper(variant, *positional_args, **kwargs)
                if sample.output_process_fn_grad is not None:
                    return sample.output_process_fn_grad(output)
                return output

            if check == 'gradcheck':
                if check_batched_grad is None:
                    check_batched_grad = op.check_batched_grad
                self.assertTrue(gradcheck(fn, gradcheck_args,
                                          check_batched_grad=check_batched_grad,
                                          check_grad_dtypes=True,
                                          nondet_tol=op.gradcheck_nondet_tol,
                                          fast_mode=op.gradcheck_fast_mode,
                                          check_forward_ad=check_forward_ad,
                                          check_backward_ad=check_backward_ad,
                                          check_undefined_grad=True,
                                          check_batched_forward_grad=check_batched_forward_grad))
            elif check in ('bwgrad_bwgrad', 'fwgrad_bwgrad'):  # gradgrad check
                self.assertFalse(check_forward_ad, msg="Cannot run forward AD check for gradgradcheck")
                for gen_non_contig_grad_outputs in (False, True):
                    kwargs = {
                        "gen_non_contig_grad_outputs": gen_non_contig_grad_outputs,
                        "check_batched_grad": op.check_batched_gradgrad,
                        "check_grad_dtypes": True,
                        "nondet_tol": op.gradcheck_nondet_tol,
                        "fast_mode": op.gradcheck_fast_mode
                    }
                    if check == "fwgrad_bwgrad":
                        kwargs["check_fwd_over_rev"] = True
                        kwargs["check_rev_over_rev"] = False
                        kwargs["check_batched_grad"] = False
                        kwargs["check_undefined_grad"] = False

                    self.assertTrue(gradgradcheck(fn, gradcheck_args, **kwargs))
            else:
                self.assertTrue(False, msg="Unknown check requested!")