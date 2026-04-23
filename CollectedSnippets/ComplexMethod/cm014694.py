def test_grouped_gemm_3d_2d(self, strided, a_row_major, b_row_major, dtype):
        device = "cuda"
        s_int = int(strided)
        m, n, k, n_groups = 16, 32, 64, 4
        if a_row_major:
            a = torch.randn(n_groups * (1 + s_int), m, k * (1 + s_int), device=device, dtype=dtype)[::(1 + s_int), :, :k]
        else:
            a = torch.randn(n_groups * (1 + s_int), k * (1 + s_int), m, device=device,
                            dtype=dtype).transpose(-2, -1)[::(1 + s_int), :, :k]
        if b_row_major:
            b = torch.randn(n * n_groups, k * (1 + s_int), device=device, dtype=dtype)[:, :k]
        else:
            b = torch.randn(k, n * (n_groups + s_int), device=device, dtype=dtype).transpose(-2, -1)[:n * n_groups, :]

        a.requires_grad_(True)
        b.requires_grad_(True)

        a_contig = a if a_row_major else a.transpose(-2, -1)
        self.assertTrue(a_contig.is_contiguous() is not strided)
        b_contig = b if b_row_major else b.transpose(-2, -1)
        self.assertTrue(b_contig.is_contiguous() is not strided)
        for check_zero_size in (False, True):
            if check_zero_size and n_groups <= 1:
                continue

            offs = torch.arange(n, n_groups * n + 1, n, device=device, dtype=torch.int32)
            if check_zero_size:
                offs[0] = offs[1]

            f = F.grouped_mm
            out = f(a, b.transpose(-2, -1), offs=offs, out_dtype=dtype)
            gO = torch.rand_like(out)
            if not check_zero_size:
                out.backward(gO)
            offs_cpu = offs.cpu()
            blist, outlist, bgradlist, gOlist = [], [], [], []
            agradlist = [None] * n_groups if check_zero_size else a.grad
            start = 0
            for i in range(n_groups):
                blist.append(b[start:offs_cpu[i]])
                bgradlist.append(b.grad[start:offs_cpu[i]])
                outlist.append(out[:, start:offs_cpu[i]])
                gOlist.append(gO[:, start:offs_cpu[i]])
                start = offs_cpu[i]
            self.grouped_mm_helper(a, blist, gOlist, agradlist, bgradlist, outlist)