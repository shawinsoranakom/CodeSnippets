def test_gradcheck_check_forward_or_backward_only(self):
        """Depending on settings for check_forward_ad and check_backward_ad, the
        correct codepaths should be reached (or not reached)
        """
        fwd_fail_err_msg = "FAIL FWD"
        bwd_fail_err_msg = "FAIL BWD"

        class UserFn(Function):
            @staticmethod
            def forward(ctx, foo, fwd_bad, bwd_bad):
                ctx.fwd_bad = fwd_bad
                ctx.bwd_bad = bwd_bad
                return foo * 2

            @staticmethod
            def vjp(ctx, gO):
                if ctx.bwd_bad:
                    raise RuntimeError(bwd_fail_err_msg)
                else:
                    return 2 * gO, None, None

            @staticmethod
            def jvp(ctx, gI, _1, _2):
                if ctx.fwd_bad:
                    raise RuntimeError(fwd_fail_err_msg)
                else:
                    return 2 * gI

        for fast_mode in (True, False):
            for check_forward_ad in (True, False):
                for check_backward_ad in (True, False):
                    for fwd_bad in (True, False):
                        for bwd_bad in (True, False):
                            fwd_should_fail = fwd_bad and check_forward_ad
                            bwd_should_fail = bwd_bad and check_backward_ad

                            def run():
                                gradcheck(
                                    UserFn.apply,
                                    (x, fwd_bad, bwd_bad),
                                    check_forward_ad=check_forward_ad,
                                    check_backward_ad=check_backward_ad,
                                    check_undefined_grad=check_backward_ad,
                                    check_batched_grad=check_backward_ad,
                                    fast_mode=fast_mode,
                                )

                            x = torch.rand(2, dtype=torch.double, requires_grad=True)

                            if not check_forward_ad and not check_backward_ad:
                                with self.assertRaisesRegex(
                                    AssertionError, "Expected at least one of"
                                ):
                                    run()
                                continue

                            if not fwd_should_fail and not bwd_should_fail:
                                run()
                            else:
                                # If both fail, backward AD failure "hides" forward AD failure
                                if fwd_should_fail:
                                    fail_msg = fwd_fail_err_msg
                                if bwd_should_fail:
                                    fail_msg = bwd_fail_err_msg
                                with self.assertRaisesRegex(RuntimeError, fail_msg):
                                    run()