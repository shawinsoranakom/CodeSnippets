def test_gather_large(self, device, dtype):
        # test larger shapes to check vectorized implementation
        for (m, n, k) in ((4096, 3072, 4096), (4096, 3072, 4100), (4, 4, 16384 * 8192)):
            torch.cuda.empty_cache()
            src = make_tensor((m, k), device=device, dtype=dtype)
            alloc0 = torch.empty(src.nelement() * 2, device=device, dtype=dtype)
            discontig = alloc0.view(m, 2 * k)[:, ::2].copy_(src)
            alloc1 = torch.empty(src.nelement() + 1, device=device, dtype=dtype)
            misaligned = alloc1[1:].view(m, k).copy_(src)
            alloc2 = torch.empty(m, k + 4, device=device, dtype=dtype)
            misaligned1 = alloc2[:, :-4].copy_(src)
            num_ind = n
            for dim in (0, 1):
                max_ind = src.shape[dim]
                ind0 = torch.randint(max_ind, (num_ind,), device=device)
                ind_discontig0 = torch.empty(num_ind * 2, device=device, dtype=torch.int64)[::2].copy_(ind0)
                shape_ind = [1] * src.ndim
                shape_ind[dim] = ind0.shape[0]
                shape_out = list(src.shape)
                shape_out[dim] = ind0.shape[0]
                ind = ind0.view(shape_ind).expand(shape_out)
                ind_discontig = ind_discontig0.view(shape_ind).expand(shape_out)
                res = torch.gather(src, dim=dim, index=ind)
                ref = src[ind0] if dim == 0 else src[:, ind0]
                self.assertEqual(res, ref, atol=0, rtol=0)
                if res.device.type == "cuda":
                    ref_cpu = src.cpu()[ind0.cpu()] if dim == 0 else src.cpu()[:, ind0.cpu()]
                    self.assertEqual(res.cpu(), ref_cpu, atol=0, rtol=0)
                res = torch.gather(src, dim=dim, index=ind_discontig)
                self.assertEqual(res, ref, atol=0, rtol=0)
                res_ind = src[ind_discontig0] if dim == 0 else src[:, ind_discontig0]
                self.assertEqual(res_ind, ref, atol=0, rtol=0)
                res_ind_neg = src[ind0 - src.shape[dim]] if dim == 0 else src[:, ind0 - src.shape[1]]
                self.assertEqual(res_ind_neg, ref, atol=0, rtol=0)
                res = torch.gather(discontig, dim=dim, index=ind)
                self.assertEqual(res, ref, atol=0, rtol=0)
                res_ind = discontig[ind0] if dim == 0 else discontig[:, ind0]
                self.assertEqual(res_ind, ref, atol=0, rtol=0)
                res = torch.gather(misaligned, dim=dim, index=ind)
                self.assertEqual(res, ref, atol=0, rtol=0)
                res_ind = misaligned[ind0] if dim == 0 else misaligned[:, ind0]
                self.assertEqual(res_ind, ref, atol=0, rtol=0)
                res_ind = misaligned1[ind0] if dim == 0 else misaligned[:, ind0]
                self.assertEqual(res_ind, ref, atol=0, rtol=0)
                res_gather = torch.gather(misaligned1, dim=dim, index=ind)
                self.assertEqual(res_gather, ref, atol=0, rtol=0)
            del src, alloc0, alloc1, alloc2
            del discontig, misaligned, misaligned1
        # test gather along 1st dim that can accidentally trigger fast path
        # because due to index dimension in the gather dim being 1
        # an unexpected squashing in tensorIterator happens
        src = make_tensor((16, 2, 16), device=device, dtype=dtype)
        ind = torch.randint(2, (16, 1), device=device).view(16, 1, 1).expand(16, 1, 16)
        res = torch.gather(src, dim=1, index=ind)
        if res.device.type == "cuda":
            ref_cpu = torch.gather(src.cpu(), dim=1, index=ind.cpu())
            self.assertEqual(res.cpu(), ref_cpu, atol=0, rtol=0)