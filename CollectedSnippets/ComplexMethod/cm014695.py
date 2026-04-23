def test_grouped_gemm_compiled(self, op, a_row_major, b_row_major, max_autotune):
        device = "cuda"
        dtype_AB = torch.bfloat16
        dtype_offset = torch.int32

        align = 16 // dtype_AB.itemsize

        f_ref = F.grouped_mm

        options = {}
        if max_autotune:
            options.update(
                {
                    "max_autotune": True,
                    "max_autotune_gemm_backends": "TRITON",
                }
            )
        f = torch.compile(
            f_ref,
            options=options,
        )

        if op == "2d/2d":
            m, n = 3, 7
            m_align = (m + align - 1) // align * align
            n_align = (n + align - 1) // align * align
            if not a_row_major and not b_row_major:
                offs = torch.tensor([0, 1, 6, 6, 7], device=device, dtype=dtype_offset)
            else:
                offs = torch.tensor([0, 8, 16, 16, 27], device=device, dtype=dtype_offset)
            ngroups = offs.shape[0]
            k = offs[-1]
            k_align = (k + align - 1) // align * align

            if a_row_major:
                A = torch.randn(m, k_align, device=device, dtype=dtype_AB)[:, :k]
            else:
                A = torch.randn(k, m_align, device=device, dtype=dtype_AB).t()[:m, :]
            if b_row_major:
                B = torch.randn(n, k_align, device=device, dtype=dtype_AB)[:, :k]
            else:
                B = torch.randn(k, n_align, device=device, dtype=dtype_AB).t()[:n, :]
        elif op == "2d/3d":
            n, k = 7, 259  # k is larger here, to validate iterating over k tiles on an op
            n_align = (n + align - 1) // align * align
            k_align = (k + align - 1) // align * align
            if a_row_major:
                offs = torch.tensor([0, 1, 3, 3, 5], device=device, dtype=dtype_offset)
            else:
                offs = torch.tensor([0, 8, 16, 16, 19], device=device, dtype=dtype_offset)
            ngroups = offs.shape[0]
            m = offs[-1]
            m_align = (m + align - 1) // align * align

            if a_row_major:
                A = torch.randn(m, k_align, device=device, dtype=dtype_AB)[:, :k]
            else:
                A = torch.randn(k, m_align, device=device, dtype=dtype_AB).t()[:m, :]
            if b_row_major:
                B = torch.randn(ngroups, n, k_align, device=device, dtype=dtype_AB)[:, :, :k]
            else:
                B = torch.randn(ngroups, k, n_align, device=device, dtype=dtype_AB).transpose(
                    -2, -1
                )[:, :n, :]
        elif op == "3d/2d":
            m, k = 3, 13
            m_align = (m + align - 1) // align * align
            k_align = (k + align - 1) // align * align
            offs = torch.tensor([0, 8, 16, 16, 19], device=device, dtype=dtype_offset)
            ngroups = offs.shape[0]
            n = offs[-1]
            n_align = (n + align - 1) // align * align

            if a_row_major:
                A = torch.randn(ngroups, m, k_align, device=device, dtype=dtype_AB)[:, :, :k]
            else:
                A = torch.randn(ngroups, k, m_align, device=device, dtype=dtype_AB).transpose(
                    -2, -1
                )[:, :m, :]
            if b_row_major:
                B = torch.randn(n, k_align, device=device, dtype=dtype_AB)[:, :k]
            else:
                B = torch.randn(k, n_align, device=device, dtype=dtype_AB).t()[:n, :]
        elif op == "3d/3d":
            offs = None
            ngroups = 5
            m, n, k = 3, 7, 13
            m_align = (m + align - 1) // align * align
            n_align = (n + align - 1) // align * align
            k_align = (k + align - 1) // align * align
            if a_row_major:
                A = torch.randn(ngroups, m, k_align, device=device, dtype=dtype_AB)[:, :, :k]
            else:
                A = torch.randn(ngroups, k, m_align, device=device, dtype=dtype_AB).transpose(
                    -2, -1
                )[:, :m, :]
            if b_row_major:
                B = torch.randn(ngroups, n, k_align, device=device, dtype=dtype_AB)[:, :, :k]
            else:
                B = torch.randn(ngroups, k, n_align, device=device, dtype=dtype_AB).transpose(
                    -2, -1
                )[:, :n, :]
        else:
            raise AssertionError(f"Invalid op: {op}")

        C_ref = f_ref(A, B.transpose(-2, -1), offs=offs)
        if not IS_BIG_GPU and max_autotune:
            with self.assertRaisesRegex(torch._inductor.exc.InductorError, "NoValidChoicesError"):
                C = f(A, B.transpose(-2, -1), offs=offs)
        else:
            C = f(A, B.transpose(-2, -1), offs=offs)
            self.assertEqual(C, C_ref)