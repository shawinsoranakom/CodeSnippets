def run_tests(fn):
            for fn_type in ("normal", "multi_view", "custom"):
                for grad_mode_view in (True, False):
                    for grad_mode_iview in (True, False):
                        for requires_grad in (True, False):
                            error1 = None  # expected error when we do inplace_view on original view
                            error2 = None  # expected error when we do inplace on the resulting view

                            if requires_grad:
                                if not grad_mode_view and grad_mode_iview:
                                    error1 = no_grad_err
                                if not grad_mode_view and not grad_mode_iview:
                                    error2 = no_grad_err

                                if fn_type == "multi_view":
                                    if grad_mode_view and grad_mode_iview:
                                        error1 = multi_view_err
                                    if grad_mode_view and not grad_mode_iview:
                                        error2 = multi_view_err

                                if fn_type == "custom":
                                    if grad_mode_view and grad_mode_iview:
                                        error1 = custom_err
                                    if grad_mode_view and not grad_mode_iview:
                                        error2 = custom_err

                            run_test(
                                fn,
                                fn_type,
                                grad_mode_view,
                                grad_mode_iview,
                                requires_grad,
                                error1,
                                error2,
                            )