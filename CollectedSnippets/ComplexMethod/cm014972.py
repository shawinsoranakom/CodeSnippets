def test_simple_zero_length(self, device, dtypes):
        val_dtype, length_type = dtypes
        lengths = [0, 0]
        data = torch.ones(0)

        for reduction in reductions:
            for initial in [0, None]:
                check_backward = initial is not None
                initial_value = initial
                default_value = get_default_value(initial_value, reduction)
                if reduction == "max":
                    expected_result = [default_value, default_value]
                    expected_grad = []
                elif reduction == "mean":
                    expected_result = [default_value, default_value]
                    expected_grad = []
                elif reduction == "min":
                    if initial is not None:
                        initial_value = 1000  # some high number
                        default_value = get_default_value(initial_value, reduction)
                    expected_result = [default_value, default_value]
                    expected_grad = []
                elif reduction == "sum":
                    expected_result = [default_value, default_value]
                    expected_grad = []
                elif reduction == "prod":
                    if initial is not None:
                        initial_value = 2  # 0 initial_value will zero out everything for prod
                        default_value = get_default_value(initial_value, reduction)
                        expected_result = [default_value, default_value]
                        expected_grad = []
                    else:
                        expected_result = [default_value, default_value]
                        expected_grad = []
                for axis in [0]:
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