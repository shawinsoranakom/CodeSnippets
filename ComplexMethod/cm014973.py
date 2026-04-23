def test_multi_d_simple(self, device, dtypes):
        val_dtype, _ = dtypes
        axis = 0
        lengths = [1, 2, 3, 0]
        data = [[1, 1], [float("nan"), 1], [3, float("nan")], [4, 1], [3, 2], [2, 3]]

        for reduction in reductions:
            for initial in [0, None]:
                check_backward = initial is not None
                initial_value = initial
                default_value = get_default_value(initial_value, reduction)
                if reduction == "max":
                    expected_result = [
                        [1, 1],
                        [float("nan"), float("nan")],
                        [4, 3],
                        [default_value, default_value],
                    ]
                    expected_grad = [
                        [1, 1],
                        [1, 0],
                        [0, 1],
                        [1, 0],
                        [0, 0],
                        [0, 1],
                    ]
                elif reduction == "mean":
                    expected_result = [
                        [1, 1],
                        [float("nan"), float("nan")],
                        [3, 2],
                        [default_value, default_value],
                    ]
                    expected_grad = [
                        [1.0, 1.0],
                        [0.5, 0.5],
                        [0.5, 0.5],
                        [0.333, 0.333],
                        [0.333, 0.333],
                        [0.333, 0.333],
                    ]
                elif reduction == "min":
                    if initial is not None:
                        initial_value = 1000  # some high number
                        default_value = get_default_value(initial_value, reduction)
                    expected_result = [
                        [1, 1],
                        [float("nan"), float("nan")],
                        [2, 1],
                        [default_value, default_value],
                    ]
                    expected_grad = [
                        [1.0, 1.0],
                        [1, 0],
                        [0, 1],
                        [0, 1],
                        [0, 0],
                        [1, 0],
                    ]
                elif reduction == "sum":
                    expected_result = [
                        [1, 1],
                        [float("nan"), float("nan")],
                        [9, 6],
                        [default_value, default_value],
                    ]
                    expected_grad = [
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 1.0],
                    ]
                elif reduction == "prod":
                    if initial is not None:
                        initial_value = 2  # 0 initial_value will zero out everything for prod
                        default_value = get_default_value(initial_value, reduction)
                        expected_result = [
                            [2, 2],
                            [float("nan"), float("nan")],
                            [48, 12],
                            [default_value, default_value],
                        ]
                        expected_grad = [
                            [2.0, 2.0],
                            [6.0, float("nan")],
                            [float("nan"), 2.0],
                            [12.0, 12.0],
                            [16.0, 6.0],
                            [24.0, 4.0],
                        ]
                    else:
                        expected_result = [
                            [1, 1],
                            [float("nan"), float("nan")],
                            [24, 6],
                            [default_value, default_value],
                        ]
                        expected_grad = [
                            [1.0, 1.0],
                            [3.0, float("nan")],
                            [float("nan"), 1.0],
                            [6.0, 6.0],
                            [8.0, 3.0],
                            [12.0, 2.0],
                        ]
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
                    )