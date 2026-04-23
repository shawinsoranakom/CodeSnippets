def test_gradcheck_mm(self, layout, dtype, device, masked, fast_mode):
        # This function does not check the following cases:
        # - batch or hybrid tensors because addmm does not support
        #   such inputs yet
        # - check_forward_ad=True because of the lack of sparse tensor
        #   support in aten::view_as_real, torch._VF._make_dual, etc.

        ref_x = torch.tensor([[1, 2, 0, 0],
                              [0, 6, 0, 0],
                              [0, 0, 0, 0],
                              [13, 14, 0, 15]], dtype=dtype, device=device)
        ref_y = torch.tensor([[11, 12, 13, 14],
                              [21, 22, 23, 24],
                              [31, 32, 33, 34],
                              [41, 42, 43, 44]],
                             dtype=dtype, device=device)

        mm = torch.sparse.mm if masked else torch.mm

        blocksize = (2, 2) if layout in {torch.sparse_bsr, torch.sparse_bsc} else None
        x = ref_x.to_sparse(layout=layout, blocksize=blocksize).requires_grad_(True)
        y = ref_y.requires_grad_(True)

        if layout is torch.sparse_bsr and not masked or layout is torch.sparse_bsc:
            with self.assertRaisesRegex(
                    RuntimeError,
                    r"addmm: computation on (CPU|CUDA) is not implemented for Strided \+ Sparse(Bsr|Bsc) @ Strided"):
                torch.autograd.gradcheck(mm, (x, y), fast_mode=fast_mode, masked=masked)
            self.skipTest('NOT IMPL')
        elif layout in {torch.sparse_csc, torch.sparse_bsr, torch.sparse_bsc} and masked:
            with self.assertRaisesRegex(
                    RuntimeError,
                    r"(sparse_addmm_sparse_backward: unsupported combination of layouts,"
                    r" grad: Strided, mat1: Sparse(Csc|Bsr|Bsc), mat2: Strided"
                    r"|addmm: computation on (CPU|CUDA) is not implemented for "
                    r"Strided \+ Sparse(Csc|Bsr|Bsc) @ Strided without MKL)"):
                torch.autograd.gradcheck(mm, (x, y), fast_mode=fast_mode, masked=masked)
            self.skipTest('NOT IMPL')
        else:
            torch.autograd.gradcheck(mm, (x, y), fast_mode=fast_mode, masked=masked)