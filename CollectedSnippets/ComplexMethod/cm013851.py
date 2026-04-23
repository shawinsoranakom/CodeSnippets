def get_multiplier() -> float:
                    # In some particular cases, we expect high difference in results.
                    # At the moment one of this cases is inductor freezing bfloat16 convolution const folding.
                    # In case of it the res_error is at least one order of magnitude higher.
                    if force_max_multiplier:
                        return 10.0
                    # In the case of using AMP (Automatic Mixed Precision), certain models have
                    # failed the benchmark's correctness check. However, the end-to-end model's
                    # accuracy when comparing AMP with FP32 is within a difference of less than 0.1%.
                    # Thus, it's possible that the correctness check failures for these models are
                    # false alarms. We use multiplier of 3 instead of 2 to avoid these false alarms.
                    multiplier = (
                        3.0 if res.dtype in (torch.float16, torch.bfloat16) else 2.0
                    )

                    if use_larger_multiplier_for_smaller_tensor and (
                        fp64_ref.numel() <= 10
                    ):
                        multiplier = 10.0
                    elif use_larger_multiplier_for_smaller_tensor and (
                        fp64_ref.numel() <= 500
                    ):
                        multiplier = 8.0
                    elif (
                        fp64_ref.numel() < 1000
                        or (ref.ndim == 4 and ref.shape[-1] == ref.shape[-2] == 1)
                        # large tol means a benchmark has been specified as REQUIRE_HIGHER_TOLERANCE
                        or tol >= 2 * 1e-2
                    ):
                        # In the presence of noise, noise might dominate our error
                        # metric for smaller tensors.
                        # Similarly, for 1x1 kernels, there seems to be high noise with amp.
                        multiplier = 3.0
                    return multiplier