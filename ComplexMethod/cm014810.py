def test_abs_angle_complex_to_float(self, device, dtype):
        # Constructs random complex values
        from random import random

        random_vals = []
        for multiplier in (-1, 1, -10, 10, -100, 100):
            for _ in range(10):
                random_vals.append(
                    complex(random() * multiplier, random() * multiplier)
                )

        for vals in (random_vals, []):
            a = np.array(vals, dtype=torch_to_numpy_dtype_dict[dtype])
            t = torch.tensor(vals, device=device, dtype=dtype)

            for fn_name in ("abs", "angle"):
                torch_fn = getattr(torch, fn_name)
                np_fn = getattr(np, fn_name)

                # Tests function
                np_result = torch.from_numpy(np_fn(a))
                torch_result = torch_fn(t).cpu()
                self.assertEqual(np_result, torch_result, exact_dtype=True)

                # Tests float out
                float_dtype = (
                    torch.float32 if dtype is torch.complex64 else torch.float64
                )
                np_float_out = np_fn(a).astype(torch_to_numpy_dtype_dict[float_dtype])
                float_out = torch.empty_like(t, dtype=float_dtype)
                torch_fn(t, out=float_out)
                self.assertEqual(torch.from_numpy(np_float_out), float_out.cpu())

                # Tests float out (resized out)
                float_out = torch.empty(1, device=device, dtype=float_dtype)
                torch_fn(t, out=float_out)
                self.assertEqual(torch.from_numpy(np_float_out), float_out.cpu())

                # Tests complex out
                np_complex_out = np_fn(a).astype(torch_to_numpy_dtype_dict[dtype])
                complex_out = torch.empty_like(t)
                torch_fn(t, out=complex_out)
                self.assertEqual(torch.from_numpy(np_complex_out), complex_out.cpu())

                # Tests complex out (resized out)
                complex_out = torch.empty(0, device=device, dtype=dtype)
                torch_fn(t, out=complex_out)
                self.assertEqual(torch.from_numpy(np_complex_out), complex_out.cpu())

                # Tests long out behavior (expected failure)
                long_out = torch.empty(0, device=device, dtype=torch.long)
                with self.assertRaises(RuntimeError):
                    torch_fn(t, out=long_out)

                # Tests inplace
                if fn_name == "abs":
                    torch_inplace_method = getattr(torch.Tensor, fn_name + "_")
                    np_fn(a, out=a)
                    if dtype.is_complex:
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "In-place abs is not supported for complex tensors.",
                        ):
                            torch_inplace_method(t)
                        return
                    torch_inplace_method(t)
                    self.assertEqual(torch.from_numpy(a), t.cpu())

                # Note: angle does not have an in-place variant
                if fn_name == "angle":
                    with self.assertRaises(AttributeError):
                        torch_inplace_method = getattr(torch.Tensor, fn_name + "_")