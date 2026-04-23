def test_type_promotion(self, device, op):
        supported_dtypes = op.supported_dtypes(torch.device(device).type)
        make_lhs = partial(
            make_tensor, (5,), device=device, **op.lhs_make_tensor_kwargs
        )
        make_rhs = partial(
            make_tensor, (5,), device=device, **op.rhs_make_tensor_kwargs
        )

        make_rhs_scalar_tensor = partial(
            make_tensor, (), device="cpu", **op.rhs_make_tensor_kwargs
        )

        def _supported(dtypes):
            return all(x in supported_dtypes for x in dtypes)

        # int x int type promotion
        if _supported((torch.int16, torch.int32, torch.int64)):
            lhs_i16 = make_lhs(dtype=torch.int16)
            lhs_i32 = make_lhs(dtype=torch.int32)
            lhs_i64 = make_lhs(dtype=torch.int64)

            rhs_i16 = make_rhs(dtype=torch.int16)
            rhs_i32 = make_rhs(dtype=torch.int32)
            rhs_i64 = make_rhs(dtype=torch.int64)

            if op.promotes_int_to_float:
                default_dtype = torch.get_default_dtype()
                self.assertEqual(op(lhs_i16, rhs_i32).dtype, default_dtype)
                self.assertEqual(
                    op(lhs_i16, rhs_i32),
                    op(lhs_i16.to(default_dtype), rhs_i32.to(default_dtype)),
                )

                self.assertEqual(op(lhs_i32, rhs_i64).dtype, default_dtype)
                self.assertEqual(
                    op(lhs_i32, rhs_i64),
                    op(lhs_i32.to(default_dtype), rhs_i64.to(default_dtype)),
                )
            elif op.always_returns_bool:
                self.assertEqual(op(lhs_i16, rhs_i32).dtype, torch.bool)
                self.assertEqual(op(lhs_i32, rhs_i64).dtype, torch.bool)
            else:  # standard type promotion
                self.assertEqual(op(lhs_i16, rhs_i32).dtype, torch.int32)
                self.assertEqual(
                    op(lhs_i16, rhs_i32), op(lhs_i16.to(torch.int32), rhs_i32)
                )

                self.assertEqual(op(lhs_i32, rhs_i64).dtype, torch.int64)
                self.assertEqual(
                    op(lhs_i32, rhs_i64), op(lhs_i32.to(torch.int64), rhs_i64)
                )

            if op.supports_out:
                if not op.promotes_int_to_float:
                    # Integers can be safely cast to other integer types
                    out = torch.empty_like(lhs_i64)
                    self.assertEqual(op(lhs_i16, rhs_i32, out=out).dtype, torch.int64)
                    self.assertEqual(op(lhs_i16, rhs_i32), out, exact_dtype=False)

                    out = torch.empty_like(lhs_i16)
                    self.assertEqual(op(lhs_i32, rhs_i64, out=out).dtype, torch.int16)
                else:
                    # Float outs cannot be safely cast to integer types
                    with self.assertRaisesRegex(RuntimeError, "can't be cast"):
                        op(lhs_i16, rhs_i32, out=torch.empty_like(lhs_i64))

                if not op.always_returns_bool:
                    # Neither integer nor float outs can be cast to bool
                    with self.assertRaisesRegex(RuntimeError, "can't be cast"):
                        op(
                            lhs_i16,
                            rhs_i32,
                            out=torch.empty_like(lhs_i64, dtype=torch.bool),
                        )

                # All these output types can be cast to any float or complex type
                out = torch.empty_like(lhs_i64, dtype=torch.float16)
                self.assertEqual(op(lhs_i16, rhs_i32, out=out).dtype, torch.float16)

                out = torch.empty_like(lhs_i64, dtype=torch.bfloat16)
                self.assertEqual(op(lhs_i16, rhs_i32, out=out).dtype, torch.bfloat16)

                out = torch.empty_like(lhs_i64, dtype=torch.float32)
                self.assertEqual(op(lhs_i16, rhs_i32, out=out).dtype, torch.float32)
                self.assertEqual(op(lhs_i16, rhs_i32), out, exact_dtype=False)

                out = torch.empty_like(lhs_i64, dtype=torch.complex64)
                self.assertEqual(op(lhs_i16, rhs_i32, out=out).dtype, torch.complex64)
                self.assertEqual(op(lhs_i16, rhs_i32), out, exact_dtype=False)

        # float x float type promotion
        if _supported((torch.float32, torch.float64)):
            lhs_f32 = make_lhs(dtype=torch.float32)
            lhs_f64 = make_lhs(dtype=torch.float64)

            rhs_f32 = make_rhs(dtype=torch.float32)
            rhs_f64 = make_rhs(dtype=torch.float64)

            if op.always_returns_bool:
                self.assertEqual(op(lhs_f32, rhs_f64).dtype, torch.bool)
            else:  # normal float type promotion
                self.assertEqual(op(lhs_f32, rhs_f64).dtype, torch.float64)
                self.assertEqual(
                    op(lhs_f32, rhs_f64), op(lhs_f32.to(torch.float64), rhs_f64)
                )

            if op.supports_out:
                # All these output types can be cast to any float or complex type
                out = torch.empty_like(lhs_f64, dtype=torch.float16)
                self.assertEqual(op(lhs_f32, rhs_f64, out=out).dtype, torch.float16)

                out = torch.empty_like(lhs_f64, dtype=torch.bfloat16)
                self.assertEqual(op(lhs_f32, rhs_f64, out=out).dtype, torch.bfloat16)
                self.assertEqual(op(lhs_f32, rhs_f64), out, exact_dtype=False)

                out = torch.empty_like(lhs_f64, dtype=torch.float32)
                self.assertEqual(op(lhs_f32, rhs_f64, out=out).dtype, torch.float32)
                self.assertEqual(op(lhs_f32, rhs_f64), out, exact_dtype=False)

                out = torch.empty_like(lhs_f64, dtype=torch.complex64)
                self.assertEqual(op(lhs_f32, rhs_f64, out=out).dtype, torch.complex64)
                self.assertEqual(op(lhs_f32, rhs_f64), out, exact_dtype=False)

                if not op.always_returns_bool:
                    # float outs can't be cast to an integer dtype
                    with self.assertRaisesRegex(RuntimeError, "can't be cast"):
                        op(
                            lhs_f32,
                            rhs_f64,
                            out=torch.empty_like(lhs_f64, dtype=torch.int64),
                        )
                else:
                    # bool outs can be cast to an integer dtype
                    out = torch.empty_like(lhs_f64, dtype=torch.int64)
                    self.assertEqual(op(lhs_f32, rhs_f64, out=out).dtype, torch.int64)
                    self.assertEqual(op(lhs_f32, rhs_f64), out, exact_dtype=False)

        # complex x complex type promotion
        if _supported((torch.complex64, torch.complex128)):
            lhs_c64 = make_lhs(dtype=torch.complex64)
            lhs_c128 = make_lhs(dtype=torch.complex128)

            rhs_c64 = make_rhs(dtype=torch.complex64)
            rhs_c128 = make_rhs(dtype=torch.complex128)

            if op.always_returns_bool:
                self.assertEqual(op(lhs_c64, lhs_c128).dtype, torch.bool)
            else:  # normal complex type promotion
                self.assertEqual(op(lhs_c64, rhs_c128).dtype, torch.complex128)
                self.assertEqual(
                    op(lhs_c64, rhs_c128), op(lhs_c64.to(torch.complex128), rhs_c128)
                )

            if op.supports_out:
                # All these output types can be cast to any or complex type
                out = torch.empty_like(lhs_c64, dtype=torch.complex64)

                self.assertEqual(op(lhs_c64, rhs_c128, out=out).dtype, torch.complex64)
                result = op(lhs_c64, rhs_c128)
                self.assertEqual(result, out.to(result.dtype))

                if not op.always_returns_bool:
                    # complex outs can't be cast to float types
                    with self.assertRaisesRegex(RuntimeError, "can't be cast"):
                        op(
                            lhs_c64,
                            rhs_c128,
                            out=torch.empty_like(lhs_c64, dtype=torch.float64),
                        )
                    # complex outs can't be cast to an integer dtype
                    with self.assertRaisesRegex(RuntimeError, "can't be cast"):
                        op(
                            lhs_c64,
                            rhs_c128,
                            out=torch.empty_like(lhs_c64, dtype=torch.int64),
                        )
                else:
                    # bool outs can be cast to a float type
                    out = torch.empty_like(lhs_c64, dtype=torch.float64)
                    self.assertEqual(
                        op(lhs_c64, rhs_c128, out=out).dtype, torch.float64
                    )
                    self.assertEqual(op(lhs_c64, rhs_c128), out, exact_dtype=False)

                    # bool outs can be cast to an integer dtype
                    out = torch.empty_like(lhs_f64, dtype=torch.int64)
                    self.assertEqual(op(lhs_f32, rhs_f64, out=out).dtype, torch.int64)
                    self.assertEqual(op(lhs_f32, rhs_f64), out, exact_dtype=False)

        # int x float type promotion
        # Note: float type is the result dtype
        if _supported((torch.long, torch.float32)):
            lhs_i64 = make_lhs(dtype=torch.int64)
            rhs_f32 = make_rhs(dtype=torch.float32)

            result = op(lhs_i64, rhs_f32)
            expected_dtype = torch.float32 if not op.always_returns_bool else torch.bool
            self.assertEqual(result.dtype, expected_dtype)

        # float x complex type promotion
        # Note: complex type with highest "value type" is the result dtype
        if _supported((torch.float64, torch.complex64)):
            lhs_f64 = make_lhs(dtype=torch.float64)
            rhs_c64 = make_rhs(dtype=torch.complex64)

            result = op(lhs_f64, rhs_c64)
            expected_dtype = (
                torch.complex128 if not op.always_returns_bool else torch.bool
            )
            self.assertEqual(result.dtype, expected_dtype)

        # int x float scalar type promotion
        # Note: default float dtype is the result dtype
        if _supported((torch.int64, torch.float32)) and op.supports_rhs_python_scalar:
            lhs_i64 = make_lhs(dtype=torch.int64)
            rhs_f_scalar = 1.0

            result = op(lhs_i64, rhs_f_scalar)
            expected_dtype = (
                torch.get_default_dtype() if not op.always_returns_bool else torch.bool
            )
            self.assertEqual(result.dtype, expected_dtype)

            # repeats with a scalar float tensor, which should set the dtype
            rhs_f32_scalar_tensor = make_rhs_scalar_tensor(dtype=torch.float32)
            result = op(lhs_i64, rhs_f32_scalar_tensor)
            expected_dtype = torch.float32 if not op.always_returns_bool else torch.bool
            self.assertEqual(result.dtype, expected_dtype)

            # Additional test with double
            if _supported((torch.float64,)):
                rhs_f64_scalar_tensor = make_rhs_scalar_tensor(dtype=torch.float64)
                result = op(lhs_i64, rhs_f64_scalar_tensor)
                expected_dtype = (
                    torch.float64 if not op.always_returns_bool else torch.bool
                )
                self.assertEqual(result.dtype, expected_dtype)

        # float x complex scalar type promotion
        # Note: result dtype is complex with highest "value type" among all tensors
        if (
            _supported((torch.float32, torch.complex64))
            and op.supports_rhs_python_scalar
        ):
            lhs_f32 = make_lhs(dtype=torch.float32)
            rhs_c_scalar = complex(1, 1)

            result = op(lhs_f32, rhs_c_scalar)
            expected_dtype = (
                torch.complex64 if not op.always_returns_bool else torch.bool
            )
            self.assertEqual(result.dtype, expected_dtype)

            # repeats with a scalar complex tensor
            rhs_c64_scalar_tensor = make_rhs_scalar_tensor(dtype=torch.complex64)
            result = op(lhs_f32, rhs_c64_scalar_tensor)
            expected_dtype = (
                torch.complex64 if not op.always_returns_bool else torch.bool
            )
            self.assertEqual(result.dtype, expected_dtype)

            # Additional test with complexdouble
            if _supported((torch.complex128,)):
                rhs_c128_scalar_tensor = make_rhs_scalar_tensor(dtype=torch.complex128)
                result = op(lhs_f32, rhs_c128_scalar_tensor)
                # Value type of 1D+ Tensor (lhs_f32) takes priority over scalar tensor (rhs_c128).
                expected_dtype = (
                    torch.complex64 if not op.always_returns_bool else torch.bool
                )
                self.assertEqual(result.dtype, expected_dtype)

        # float x float scalar tensor
        # Note: result dtype is the type of the float tensor
        if _supported((torch.float32, torch.float64)) and op.supports_rhs_python_scalar:
            lhs_f32 = make_lhs(dtype=torch.float32)
            rhs_f64_scalar_tensor = make_rhs_scalar_tensor(dtype=torch.float64)

            result = op(lhs_f32, rhs_f64_scalar_tensor)
            expected_dtype = torch.float32 if not op.always_returns_bool else torch.bool
            self.assertEqual(result.dtype, expected_dtype)

        # complex x complex scalar tensor
        # Note: result dtype is the type of the complex tensor
        if (
            _supported((torch.complex64, torch.complex128))
            and op.supports_rhs_python_scalar
        ):
            lhs_c64 = make_lhs(dtype=torch.complex64)
            rhs_c128_scalar_tensor = make_rhs_scalar_tensor(dtype=torch.complex128)

            result = op(lhs_c64, rhs_c128_scalar_tensor)
            expected_dtype = (
                torch.complex64 if not op.always_returns_bool else torch.bool
            )
            self.assertEqual(result.dtype, expected_dtype)

        # scalar  x scalar
        # Note: result dtype is default float type
        if op.supports_two_python_scalars and _supported((torch.long, torch.float32)):
            rhs_f_scalar = 2.0
            for lhs in (1, 1.0):
                result = op(lhs, rhs_f_scalar)
                expected_dtype = (
                    torch.get_default_dtype()
                    if not op.always_returns_bool
                    else torch.bool
                )
                self.assertEqual(result.dtype, expected_dtype)