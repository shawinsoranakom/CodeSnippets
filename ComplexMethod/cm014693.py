def test_grouped_gemm_2d_3d(self, strided, a_row_major, b_row_major, dtype):
        device = "cuda"
        s_int = int(strided)
        m, n, k, n_groups = 16, 32, 64, 4
        if a_row_major:
            a = torch.randn(m * n_groups, k * (1 + s_int), device=device, dtype=dtype)[:, :k]
        else:
            a = torch.randn(k, (m + 2 * s_int) * n_groups, device=device, dtype=dtype).t()[:m * n_groups, :]

        if b_row_major:
            b = torch.randn(n_groups * (1 + s_int), n, k * (1 + s_int), device=device, dtype=dtype)[::(1 + s_int), :, :k]
        else:
            b = torch.randn(n_groups * (1 + s_int), k * (1 + s_int), n, device=device,
                            dtype=dtype).transpose(-2, -1)[::(1 + s_int), :, :k]

        a.requires_grad_(True)
        b.requires_grad_(True)

        a_contig = a if a_row_major else a.t()
        self.assertTrue(a_contig.is_contiguous() is not strided)
        b_contig = b if b_row_major else b.transpose(-2, -1)
        self.assertTrue(b_contig.is_contiguous() is not strided)
        for check_zero_size in (False, True):
            if check_zero_size and n_groups <= 1:
                continue

            a.grad = None
            b.grad = None
            offs = torch.arange(m, n_groups * m + 1, m, device=device, dtype=torch.int32)
            if check_zero_size:
                offs[0] = offs[1]

            f = F.grouped_mm
            out = f(a, b.transpose(-2, -1), offs=offs, out_dtype=dtype)
            gO = torch.rand_like(out)
            if not check_zero_size:
                out.backward(gO)
            offs_cpu = offs.cpu()
            alist, agradlist, gOlist, outlist = [], [], [], []
            bgradlist = [None] * n_groups if check_zero_size else b.grad
            start = 0
            for i in range(n_groups):
                alist.append(a[start:offs_cpu[i]])
                agradlist.append(None if check_zero_size else a.grad[start:offs_cpu[i]])
                outlist.append(out[start:offs_cpu[i]])
                gOlist.append(gO[start:offs_cpu[i]])
                start = offs_cpu[i]
            self.grouped_mm_helper(alist, b, gOlist, agradlist, bgradlist, outlist)