def test_float8_error_messages(self, device) -> None:
        M, K, N = (1024, 512, 2048)
        fill_value = 0.5
        x = torch.full((M, K), fill_value, device=device)
        y = torch.full((N, K), fill_value, device=device)

        x_fp8 = x.to(e4m3_type)
        y_fp8 = y.to(e4m3_type).t()

        with self.assertRaisesRegex(
            ValueError, re.escape("scale_b must have 1 Float element")
        ):
            scaled_mm_wrap(
                x_fp8,
                y_fp8,
                scale_a=torch.ones((1, 1), device=device),
                scale_b=torch.ones((1, 2), device=device),
                scale_recipe_a=ScalingType.TensorWise,
                scale_recipe_b=ScalingType.TensorWise,
                out_dtype=torch.bfloat16,
            )

        with self.assertRaisesRegex(
            ValueError, re.escape(f"scale_b must have {N} Float elements, got {N + 1}"),
        ):
            scaled_mm_wrap(
                x_fp8,
                y_fp8,
                scale_a=torch.ones((M, 1), device=device),
                scale_b=torch.ones((1, N + 1), device=device),
                scale_recipe_a=ScalingType.RowWise,
                scale_recipe_b=ScalingType.RowWise,
                out_dtype=torch.bfloat16,
            )
        with self.assertRaisesRegex(
            IndexError, re.escape("Dimension out of range")
        ):
            scaled_mm_wrap(
                x_fp8,
                y_fp8,
                scale_a=torch.ones((M), device=device),
                scale_b=torch.ones((N, 1), device=device),
                scale_recipe_a=ScalingType.RowWise,
                scale_recipe_b=ScalingType.RowWise,
                out_dtype=torch.bfloat16,
            )

        with self.assertRaisesRegex(
            ValueError, re.escape("expected scale_b.stride(1) to be 1, but got 2"),
        ):
            scaled_mm_wrap(
                x_fp8,
                y_fp8,
                scale_a=torch.ones((M, 1), device=device),
                scale_b=torch.ones((1, N * 2), device=device)[:, ::2],
                scale_recipe_a=ScalingType.RowWise,
                scale_recipe_b=ScalingType.RowWise,
                out_dtype=torch.bfloat16,
            )

        def e5m2():
            out = scaled_mm_wrap(
                x_fp8,
                y_fp8.to(e5m2_type),
                scale_a=torch.ones((M, 1), device=device),
                scale_b=torch.ones((1, N), device=device),
                out_dtype=torch.bfloat16,
            )
            return out

        if (torch.xpu.is_available() or
            (torch.cuda.is_available() and
             torch.cuda.get_device_capability() == (9, 0) and
             torch.version.cuda and
             torch.version.cuda >= "12.9") or (not torch.cuda.is_available() and torch.cpu.is_available())):
            out = e5m2()
            self.assertEqual(out, torch.ones_like(out) * 128.)
        else:
            if torch.version.hip:
                # Note re.compile is used, not re.escape. This is to accommodate fn vs fnuz type message.
                with self.assertRaisesRegex(
                    ValueError,
                    r"expected mat_b\.dtype\(\) to be at::kFloat8_e4m3fn(uz)?, but got c10::Float8_e5m2(fnuz)?"
                ):
                    e5m2()
            else:
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"Expected b\.dtype\(\) == at::kFloat8_e4m3fn to be true, but got false\.",
                ):
                    e5m2()