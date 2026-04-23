def test_jvp(self, device, dtype, op):
        # TODO: get rid of vjp_decomp when we add decomposition support to
        # PyTorch's forward-mode ad. Currently the decomposition support only
        # works for functorch.jvp
        VJP_DECOMP = {
            "nn.functional.logsigmoid",
        }
        if op.name in VJP_DECOMP:
            fixme_ref_jvp_local = simulate_jvp
        else:
            fixme_ref_jvp_local = ref_jvp

        if not op.supports_forward_ad and op.name not in VJP_DECOMP:
            self.skipTest("Skipped! Forward AD not supported.")
            return

        samples = op.sample_inputs(device, dtype, requires_grad=True)

        outplace_variant = op if not is_inplace(op, op.get_op()) else None
        inplace_variant = op.inplace_variant if op.supports_inplace_autograd else None

        for sample in samples:
            if outplace_variant:
                self.jvp_opinfo_test(
                    outplace_variant,
                    sample,
                    sample.output_process_fn_grad,
                    clone_inputs=False,
                    fixme_ref_jvp_local=fixme_ref_jvp_local,
                    test_noncontig=op.name not in skip_noncontig,
                )
            if is_valid_inplace_sample_input(sample, op, inplace_variant):
                self.jvp_opinfo_test(
                    inplace_variant,
                    sample,
                    sample.output_process_fn_grad,
                    clone_inputs=True,
                    fixme_ref_jvp_local=fixme_ref_jvp_local,
                    test_noncontig=op.name not in skip_noncontig,
                )