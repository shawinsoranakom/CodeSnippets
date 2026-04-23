def test_numpy_array_interface(self, device):
        types = [
            torch.DoubleTensor,
            torch.FloatTensor,
            torch.HalfTensor,
            torch.LongTensor,
            torch.IntTensor,
            torch.ShortTensor,
            torch.ByteTensor,
        ]
        dtypes = [
            np.float64,
            np.float32,
            np.float16,
            np.int64,
            np.int32,
            np.int16,
            np.uint8,
        ]
        for tp, dtype in zip(types, dtypes):
            # Only concrete class can be given where "Type[number[_64Bit]]" is expected
            if np.dtype(dtype).kind == "u":  # type: ignore[misc]
                # .type expects a XxxTensor, which have no type hints on
                # purpose, so ignore during mypy type checking
                x = torch.tensor([1, 2, 3, 4]).type(tp)  # type: ignore[call-overload]
                array = np.array([1, 2, 3, 4], dtype=dtype)
            else:
                x = torch.tensor([1, -2, 3, -4]).type(tp)  # type: ignore[call-overload]
                array = np.array([1, -2, 3, -4], dtype=dtype)

            # Test __array__ w/o dtype argument
            asarray = np.asarray(x)
            self.assertIsInstance(asarray, np.ndarray)
            self.assertEqual(asarray.dtype, dtype)
            for i in range(len(x)):
                self.assertEqual(asarray[i], x[i])

            # Test __array_wrap__, same dtype
            abs_x = np.abs(x)
            abs_array = np.abs(array)
            self.assertIsInstance(abs_x, tp)
            for i in range(len(x)):
                self.assertEqual(abs_x[i], abs_array[i])

        # Test __array__ with dtype argument
        for dtype in dtypes:
            x = torch.IntTensor([1, -2, 3, -4])
            asarray = np.asarray(x, dtype=dtype)
            self.assertEqual(asarray.dtype, dtype)
            # Only concrete class can be given where "Type[number[_64Bit]]" is expected
            if np.dtype(dtype).kind == "u":  # type: ignore[misc]
                wrapped_x = np.array([1, -2, 3, -4]).astype(dtype)
                for i in range(len(x)):
                    self.assertEqual(asarray[i], wrapped_x[i])
            else:
                for i in range(len(x)):
                    self.assertEqual(asarray[i], x[i])

        # Test some math functions with float types
        float_types = [torch.DoubleTensor, torch.FloatTensor]
        float_dtypes = [np.float64, np.float32]
        for tp, dtype in zip(float_types, float_dtypes):
            x = torch.tensor([1, 2, 3, 4]).type(tp)  # type: ignore[call-overload]
            array = np.array([1, 2, 3, 4], dtype=dtype)
            for func in ["sin", "sqrt", "ceil"]:
                ufunc = getattr(np, func)
                res_x = ufunc(x)
                res_array = ufunc(array)
                self.assertIsInstance(res_x, tp)
                for i in range(len(x)):
                    self.assertEqual(res_x[i], res_array[i])

        # Test functions with boolean return value
        for tp, dtype in zip(types, dtypes):
            x = torch.tensor([1, 2, 3, 4]).type(tp)  # type: ignore[call-overload]
            array = np.array([1, 2, 3, 4], dtype=dtype)
            geq2_x = np.greater_equal(x, 2)
            geq2_array = np.greater_equal(array, 2).astype("uint8")
            self.assertIsInstance(geq2_x, torch.ByteTensor)
            for i in range(len(x)):
                self.assertEqual(geq2_x[i], geq2_array[i])