def test_multi_d(self, device, dtypes):
        val_dtype, _ = dtypes
        axis = 0
        lengths = [0, 2, 3, 0]
        data = np.arange(50).reshape(5, 2, 5).tolist()
        expected_grad = []

        # TODO: calculate grad and check correctness
        check_backward = False

        for reduction in reductions:
            initial_value = 0
            if reduction == "max":
                expected_result = [
                    np.full((2, 5), initial_value).tolist(),
                    np.max(data[:2], axis=0).tolist(),
                    np.max(data[2:], axis=0).tolist(),
                    np.full((2, 5), initial_value).tolist(),
                ]
            elif reduction == "mean":
                expected_result = [
                    np.full((2, 5), initial_value).tolist(),
                    np.mean(data[:2], axis=0).tolist(),
                    np.mean(data[2:], axis=0).tolist(),
                    np.full((2, 5), initial_value).tolist(),
                ]
            elif reduction == "min":
                initial_value = 1000  # some high number
                expected_result = [
                    np.full((2, 5), initial_value).tolist(),
                    np.min(data[:2], axis=0).tolist(),
                    np.min(data[2:], axis=0).tolist(),
                    np.full((2, 5), initial_value).tolist(),
                ]
            elif reduction == "sum":
                expected_result = [
                    np.full((2, 5), initial_value).tolist(),
                    np.sum(data[:2], axis=0).tolist(),
                    np.sum(data[2:], axis=0).tolist(),
                    np.full((2, 5), initial_value).tolist(),
                ]
            elif reduction == "prod":
                initial_value = 1
                expected_result = [
                    np.full((2, 5), initial_value).tolist(),
                    np.prod(data[:2], axis=0).tolist(),
                    np.prod(data[2:], axis=0).tolist(),
                    np.full((2, 5), initial_value).tolist(),
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