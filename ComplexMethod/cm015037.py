def _test_inplace_preserve_storage(samples, variants):
            for sample in samples:
                # Skips inplace variants if the output dtype is not the same as
                #   the input dtype
                expected_forward = op(sample.input, *sample.args, **sample.kwargs)
                tensor = (
                    sample.input
                    if isinstance(sample.input, torch.Tensor)
                    else sample.input[0]
                )
                skip_inplace = False
                if (
                    isinstance(expected_forward, torch.Tensor)
                    and expected_forward.dtype is not tensor.dtype
                ):
                    skip_inplace = True
                if skip_inplace:
                    return
                for variant in variants:
                    cloned = (
                        clone_input_helper(sample.input)
                        if variant in inplace_ops
                        else sample.input
                    )
                    inp_tensor = (
                        cloned if isinstance(cloned, torch.Tensor) else cloned[0]
                    )
                    data_ptr = inp_tensor.data_ptr()
                    if variant in operators and sample.kwargs:
                        # skip samples with kwargs for operator variants
                        continue

                    variant_forward = variant(cloned, *sample.args, **sample.kwargs)
                    # TODO Support non-tensor outputs if they exist for inplace ops
                    if isinstance(variant_forward, torch.Tensor):
                        self.assertEqual(
                            data_ptr, variant_forward.data_ptr(), atol=0, rtol=0
                        )
                    else:
                        self.assertTrue(
                            False,
                            "Non-tensor outputs for inplace ops are not supported",
                        )