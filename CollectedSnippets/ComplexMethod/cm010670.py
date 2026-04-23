def compare_outputs(original, reference, match_what):
            all_ok = True
            for i, (orig, ref) in enumerate(zip(original, reference)):
                try:
                    if orig.is_quantized:
                        orig = orig.dequantize()
                    if ref.is_quantized:
                        ref = ref.dequantize()
                    if orig.is_mkldnn:
                        orig = orig.to_dense()
                    if ref.is_mkldnn:
                        ref = ref.to_dense()
                    if ref.is_complex() or orig.is_complex():
                        torch.testing.assert_close(
                            orig.to(torch.cdouble),
                            ref.to(torch.cdouble),
                            rtol=check_tolerance,
                            atol=default_tolerances(orig, ref)[1],
                            equal_nan=True,
                        )
                    else:
                        if orig.is_mps or ref.is_mps:
                            torch.testing.assert_close(
                                orig.float(),
                                ref.float(),
                                rtol=check_tolerance,
                                atol=default_tolerances(orig, ref)[1],
                                equal_nan=True,
                            )
                        elif getattr(orig, "is_nested", None) or getattr(
                            ref, "is_nested", None
                        ):
                            if getattr(orig, "is_nested", None) != getattr(
                                ref, "is_nested", None
                            ):
                                raise AssertionError(
                                    f"Nested tensor mismatch: orig.is_nested="
                                    f"{getattr(orig, 'is_nested', None)}, "
                                    f"ref.is_nested={getattr(ref, 'is_nested', None)}"
                                )
                            for t_orig, t_ref in zip(orig.unbind(), ref.unbind()):
                                torch.testing.assert_close(
                                    t_orig.double(),
                                    t_ref.double(),
                                    rtol=check_tolerance,
                                    atol=default_tolerances(t_orig, t_ref)[1],
                                    equal_nan=True,
                                )
                        else:
                            torch.testing.assert_close(
                                orig.double(),
                                ref.double(),
                                rtol=check_tolerance,
                                atol=default_tolerances(orig, ref)[1],
                                equal_nan=True,
                            )
                except AssertionError as e:
                    maybe_warn_nondeterministic()
                    warnings.warn(
                        "Output nr "
                        + str(i + 1)
                        + ". of the traced function does not match "
                        "the corresponding output of the "
                        + match_what
                        + ". Detailed error:\n"
                        + str(e),
                        category=TracerWarning,
                        stacklevel=4,
                    )
                    all_ok = False

            return all_ok