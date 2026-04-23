def test_pointwise(self, name, op):
        dtype = torch.float32
        check_lowp = True
        if self.device == GPU_TYPE and name in {
            "airy_ai",
            "bessel_i0",
            "bessel_i1",
            "bessel_j0",
            "bessel_j1",
            "bessel_y0",
            "bessel_y1",
            "erfcx",
            "gammainc",
            "gammaincc",
            "i1",
            "i1e",
            "modified_bessel_i0",
            "modified_bessel_i1",
            "modified_bessel_k0",
            "modified_bessel_k1",
            "ndtri",
            "scaled_modified_bessel_k0",
            "scaled_modified_bessel_k1",
            "spherical_bessel_j0",
            "zeta",
            "chebyshev_polynomial_t",
            "chebyshev_polynomial_v",
            "chebyshev_polynomial_u",
            "chebyshev_polynomial_w",
            "legendre_polynomial_p",
            "shifted_chebyshev_polynomial_t",
            "shifted_chebyshev_polynomial_u",
            "shifted_chebyshev_polynomial_v",
            "shifted_chebyshev_polynomial_w",
            "hermite_polynomial_h",
            "hermite_polynomial_he",
            "laguerre_polynomial_l",
        }:
            # <func>_cuda not implemented for Half
            check_lowp = False

        if (
            is_halide_backend(self.device)
            or is_triton_cpu_backend(self.device)
            and name
            in (
                "erfinv",
                "airy_ai",
                "bessel_j0",
                "bessel_j1",
                "bessel_y0",
                "bessel_y1",
                "chebyshev_polynomial_t",
                "chebyshev_polynomial_u",
                "chebyshev_polynomial_v",
                "chebyshev_polynomial_w",
                "digamma",
                "gammainc",
                "gammaincc",
                "gammaln",
                "hermite_polynomial_h",
                "hermite_polynomial_he",
                "i0",
                "i0e",
                "i1",
                "i1e",
                "laguerre_polynomial_l",
                "legendre_polynomial_p",
                "modified_bessel_i0",
                "modified_bessel_i1",
                "modified_bessel_k0",
                "modified_bessel_k1",
                "multigammaln",
                "ndtri",
                "polygamma",
                "psi",
                "scaled_modified_bessel_k0",
                "scaled_modified_bessel_k1",
                "shifted_chebyshev_polynomial_t",
                "shifted_chebyshev_polynomial_u",
                "shifted_chebyshev_polynomial_v",
                "shifted_chebyshev_polynomial_w",
                "spherical_bessel_j0",
                "zeta",
            )
        ):
            raise unittest.SkipTest(f"Halide & Triton CPU do not support {name}")

        if is_triton_cpu_backend(self.device) and name in [
            "erfc",
            "erfcx",
            "round",
            "log_ndtr",
        ]:
            raise unittest.SkipTest(f"Triton CPU does not support {name}")

        if is_pallas_backend(self.device) and name in {
            "airy_ai",
            "bessel_y0",
            "bessel_y1",
            "modified_bessel_k0",
            "modified_bessel_k1",
            "ndtri",
            "scaled_modified_bessel_k0",
            "scaled_modified_bessel_k1",
        }:
            raise unittest.SkipTest(f"Pallas does not support {name}")

        if name in {"gammainc", "gammaincc"}:
            args = (
                torch.randn(8, 8, dtype=dtype, device=self.device),
                torch.empty(8, 8, dtype=dtype, device=self.device).uniform_(1, 2),
            )

            def fn(x, y):
                return op(x, y)

        elif name in {"xlog1py", "xlogy", "zeta"}:
            args = (
                torch.randn(8, 8, dtype=dtype, device=self.device),
                torch.empty(8, 8, dtype=dtype, device=self.device).uniform_(1, 2),
            )

            def fn(x, y):
                return op(x, y)

        elif name == "multigammaln":
            args = (
                torch.empty(8, 8, dtype=dtype, device=self.device).uniform_(1, 2),
                2,
            )

            def fn(x, p):
                return op(x, p)

        elif name == "polygamma":
            args = (
                1,
                torch.empty(8, 8, dtype=dtype, device=self.device).uniform_(1, 10),
            )

            def fn(n, x):
                return op(n, x)

        elif "_polynomial_" in name:
            args = (
                torch.randn(8, 8, dtype=dtype, device=self.device),
                2,
            )

            def fn(x, n):
                return op(x, n)

        else:
            args = (torch.randn(8, 8, dtype=dtype, device=self.device),)

            def fn(x):
                return op(x)

        ctx = (
            contextlib.nullcontext()
            if self.device != "mps"
            or name
            not in [
                "airy_ai",
                "laguerre_polynomial_l",
                "legendre_polynomial_p",
                "log_ndtr",
                "ndtri",
            ]
            else self.assertRaises(NotImplementedError)
        )
        with ctx:
            self.common(fn, args, check_lowp=check_lowp, atol=1e-4, rtol=1e-4)