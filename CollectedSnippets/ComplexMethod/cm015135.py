def test_where_scalar_handcrafted_values(self, device):
        # Tests ScalarxScalar, ScalarxTensor and TensorxScalar
        # variant of `where` against NumPy version with
        # handcrafted values.
        condition_shape = (5, 5)
        dtypes = (
            torch.bool, torch.uint8, torch.int8, torch.int16, torch.int64,
            torch.float16, torch.float32, torch.float64,
            torch.complex64, torch.complex128,
        )
        shapes = ((), (5,), (1, 5),)

        with torch.no_grad():
            tensors = (torch.empty(shape, dtype=dtype, device=device).fill_(17)
                       for shape, dtype in product(shapes, dtypes))

        # Use different values for `x` and `y`
        # as they are the output values which are compared.
        x_vals = (True, 3, 7.0, 1 + 0.5j)
        y_vals = itertools.chain((False, 4, 8.0, 2 + 0.5j), tensors)
        for x in x_vals:
            for y in y_vals:
                condition = torch.empty(*condition_shape, dtype=torch.bool, device=device).bernoulli_()
                common_dtype = torch.result_type(x, y)

                def check_equal(condition, x, y):
                    condition_np = condition.cpu().numpy()
                    x_np = x.cpu().numpy() if isinstance(x, torch.Tensor) else x
                    y_np = y.cpu().numpy() if isinstance(y, torch.Tensor) else y

                    # NumPy aggressively promotes to double, hence cast to output to correct dtype
                    expected = torch.from_numpy(np.where(condition_np, x_np, y_np)).to(common_dtype)
                    result = torch.where(condition, x, y)
                    self.assertEqual(expected, result)

                check_equal(condition, x, y)
                check_equal(condition, y, x)
                if self.device_type == "cuda":
                    check_equal(condition, torch.tensor(x), y)
                    check_equal(condition, y, torch.tensor(x))
                    if not isinstance(y, torch.Tensor):
                        check_equal(condition, torch.tensor(y), torch.tensor(x))
                    if isinstance(y, torch.Tensor) and y.ndim > 0:
                        check_equal(torch.tensor(True), x, y)
                        check_equal(torch.tensor(True), y, x)