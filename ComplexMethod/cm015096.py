def _do_test_autograd_simple_views_python(self, dtype):
        # This is not necessarily the absolute correct behavior, but this is the current
        # one. This test is here to make sure that any change to this behavior is detected
        # and not silent. The TODOs below mark the places with unexpected behavior.
        # Note that any change in these test will be BC-breaking and should be done carefully.

        # This checks the autograd.Function behavior when we return one or multiple outputs
        # while one of these is an input, a view of an input or of a temporary tensor.

        # This indicator is used to track how many times the backward function was called
        bw_called = [0]
        # This indicator is used to check if the argument `ga` contains non-zero values
        ga_nz = [False]

        class IdOneOutput(Function):
            @staticmethod
            def forward(ctx, a, make_view, pure_view):
                ctx._is_pure_view = pure_view
                if make_view:
                    a = a.narrow(0, 0, 2)
                else:
                    a = a.clone()
                return a

            @staticmethod
            def backward(ctx, ga):
                bw_called[0] += 1
                return ga, None, None

        class IdTwoOutput(Function):
            @staticmethod
            def forward(ctx, a, b, make_view, pure_view):
                ctx._is_pure_view = pure_view
                if make_view:
                    a = a.narrow(0, 0, 2)
                else:
                    a = a.clone()
                return a, a + b

            @staticmethod
            def backward(ctx, ga, gab):
                bw_called[0] += 1
                if ga.eq(0).all():
                    ga_nz[0] = False
                else:
                    ga_nz[0] = True
                return ga + gab, gab, None, None

        class ViewOfTemp(Function):
            @staticmethod
            def forward(ctx, a, make_view, pure_view):
                ctx._is_pure_view = pure_view
                ctx.save_for_backward(a)
                if make_view:
                    a = a.narrow(0, 0, 2)
                else:
                    a = a.clone()
                b = a.clone()
                return b.select(0, 0)

            @staticmethod
            def backward(ctx, grad):
                bw_called[0] += 1
                (a,) = ctx.saved_tensors
                res = torch.zeros_like(a)
                res.select(0, 0).copy_(grad)
                return res, None, None

        fn_id_to_inplace_on_view_err_msg = {
            "one_output": (
                "Output 0 of IdOneOutput is a view and is being "
                "modified inplace. This view was created inside a custom Function"
            ),
            "two_output": (
                "Output 0 of IdTwoOutput is a view and is being modified inplace."
                " This view is the output of a function that returns multiple views.",
                "Pure view custom Function can only have one input Tensor and one output Tensor."
                " Open an issue if you need to support more.",
            ),
            "view_of_temp": (
                "Output 0 of ViewOfTemp is a view and is being "
                "modified inplace. This view was created inside a custom Function",
                "a view of a leaf Variable that requires grad is being used in an in-place operation",
            ),
        }

        for fn_id in ["one_output", "two_output", "view_of_temp"]:
            for inplace in [True, False]:
                for make_view in [True, False]:
                    for pure_view in [True, False]:
                        # Used for special casing the tests below
                        output_is_a_view = make_view or fn_id == "view_of_temp"

                        def fn(a, b):
                            # never modify a, b inplace for gracheck
                            a = a.clone()
                            b = b.clone()
                            if fn_id == "two_output":
                                tmp1, tmp2 = IdTwoOutput.apply(
                                    a, b, make_view, pure_view
                                )
                                if inplace:
                                    tmp1 += 3
                                    tmp2 += 3
                                else:
                                    tmp1 = tmp1 + 3
                                    tmp2 = tmp2 + 3
                                tmp = tmp1 * tmp2
                            else:
                                if fn_id == "one_output":
                                    tmp = IdOneOutput.apply(a, make_view, pure_view)
                                else:
                                    tmp = ViewOfTemp.apply(a + b, make_view, pure_view)
                                if inplace:
                                    tmp += 3
                                else:
                                    tmp = tmp + 3

                            return tmp.sum()

                        a = torch.ones(2, dtype=dtype, requires_grad=True)
                        b = torch.ones(2, dtype=dtype, requires_grad=True)

                        err_msg = fn_id_to_inplace_on_view_err_msg[fn_id][
                            int(pure_view)
                        ]

                        will_raise_error = (
                            (pure_view and fn_id == "two_output")
                            or (pure_view and fn_id == "view_of_temp" and inplace)
                            or (not pure_view and inplace and output_is_a_view)
                        )

                        if will_raise_error:
                            with self.assertRaisesRegex(RuntimeError, err_msg):
                                gradcheck(fn, (a, b), check_batched_grad=False)
                        else:
                            gradcheck(fn, (a, b), check_batched_grad=False)

                        # Was the custom backward called properly
                        bw_called[0] = 0
                        ga_nz[0] = True  # For the case where the backward is called

                        expected_called = 1
                        expected_ga_nz = True

                        if will_raise_error:
                            expected_called = 0
                            with self.assertRaisesRegex(RuntimeError, err_msg):
                                fn(a, b)
                        else:
                            fn(a, b).abs().backward()

                        if (
                            fn_id == "one_output"
                            and inplace
                            and output_is_a_view
                            and pure_view
                        ):
                            # We expect the op to have been replayed and we leveraged the pure view
                            # to re-create the graph, so the original backward was not called
                            expected_called = 0

                        self.assertTrue(bw_called[0] == expected_called)
                        self.assertTrue(ga_nz[0] == expected_ga_nz)