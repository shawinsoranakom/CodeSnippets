def test_simple_1d(self, device, dtypes):
        val_dtype, length_type = dtypes
        lengths = [1, 2, 3, 0]
        data = [1, float("nan"), 3, 4, 5, 5]

        for reduction in reductions:
            for initial in [0, None]:
                check_backward = initial is not None
                initial_value = initial
                default_value = get_default_value(initial_value, reduction)
                if reduction == "max":
                    expected_result = [1, float("nan"), 5, default_value]
                    expected_grad = [1, 1, 0, 0, 0.5, 0.5]
                elif reduction == "mean":
                    expected_result = [1, float("nan"), 4.666, default_value]
                    expected_grad = [1.0, 0.5, 0.5, 0.333, 0.333, 0.333]
                elif reduction == "min":
                    if initial is not None:
                        initial_value = 1000  # some high number
                        default_value = get_default_value(initial_value, reduction)
                    expected_result = [1, float("nan"), 4, default_value]
                    expected_grad = [1.0, 1.0, 0, 1, 0, 0]
                elif reduction == "sum":
                    expected_result = [1, float("nan"), 14, default_value]
                    expected_grad = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
                elif reduction == "prod":
                    if initial is not None:
                        initial_value = 2  # 0 initial_value will zero out everything for prod
                        default_value = get_default_value(initial_value, reduction)
                        expected_result = [2, float("nan"), 200, default_value]
                        expected_grad = [2.0, 6.0, float("nan"), 50.0, 40.0, 40.0]
                    else:
                        expected_result = [1, float("nan"), 100, default_value]
                        expected_grad = [1.0, 3.0, float("nan"), 25.0, 20.0, 20.0]
                for axis in [0, -1]:
                    for unsafe in [True, False]:
                        self._test_common(
                            reduction,
                            device,
                            val_dtype,
                            unsafe,
                            axis,
                            initial_value,
                            data,
                            lengths,
                            expected_result,
                            expected_grad,
                            check_backward,
                            length_type,
                        )