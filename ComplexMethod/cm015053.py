def test_triton_bsr_dense_bmm(self, device, dtype, index_dtype, block_size):
        from functools import partial
        from torch.sparse._triton_ops import bsr_dense_mm

        def kernel_impl(*args, **kwargs):
            return bsr_dense_mm(*args, skip_checks=True, **kwargs)

        kernel = torch._TritonLibrary.registerOp(
            "_triton_bsr_dense_mm_out",
            "_triton_bsr_dense_mm_out(Tensor bsr, Tensor dense, *, Tensor(a!) out) -> Tensor(a!)",
            kernel_impl,
            "SparseCsrCUDA"
        )

        # kernel != kernel_impl means dispatch was already registered.
        # This is exactly what we need!
        self.assertTrue(kernel is not kernel_impl)

        # Note that each value in a non-zero block is in range block_size * [low^2, high^2).
        tensor = partial(make_tensor, device=device, dtype=dtype, low=0.5, high=1.5)

        # NOTE: batch dims with zero sizes are not supported in `to_sparse_bsr`.
        batches = [(), (2,), (2, 2)]
        size = [128, 256, 0]

        # Whether to make inputs orthogonal so that the product is zero
        make_orthogonal = [True, False]

        for bd, bs, m, n, k, is_ortho in itertools.product(batches, batches, size, size, size, make_orthogonal):
            bsr = tensor(bs + (m, k))
            # NOTE: do not get confused, it will be transposed
            dense = tensor(bd + (n, k))

            if is_ortho:
                bsr = torch.cat((bsr, torch.zeros_like(bsr)), dim=-1)
                dense = torch.cat((torch.zeros_like(dense), dense), dim=-1)

            bsr = bsr.to_sparse_bsr(block_size)

            if bsr.dim() == 2 and dtype != torch.float:
                # Test against linear to check dispatch
                # which takes place for torch.half and torch.bfloat16.
                res_dense = torch.nn.functional.linear(dense, bsr.to_dense())
                res_tri_out = torch.empty_like(res_dense)
                res_tri = torch.nn.functional.linear(dense, bsr, out=res_tri_out)

                # Check dispatch worked with non-trivial outputs
                if m > 0 and n > 0 and k > 0:
                    self.assertTrue(kernel.kernel_invoked)
                    kernel.kernel_invoked = False
            else:
                # Otherwise check correctness against bmm
                # since nn.linear does not support bsr.dim() > 2.
                res_dense = bsr.to_dense() @ dense.transpose(-2, -1)
                res_tri_out = torch.empty_like(res_dense)
                res_tri = kernel(bsr, dense.transpose(-2, -1), out=res_tri_out)

            self.assertTrue(res_tri is res_tri_out)
            self.assertEqual(res_tri, res_dense)

            res_dense = bsr.to_dense() @ dense.transpose(-2, -1)
            # check whether bsr_dense_mm handles different grid sizes
            # None means max possible grid size which is CUDA-dependent.
            grid_size = (None, 2, 4)
            grid_gen = itertools.product(grid_size, repeat=3)
            for grid in grid_gen:
                res_tri = torch.sparse._triton_ops.bsr_dense_mm(
                    bsr,
                    dense.transpose(-2, -1),
                    max_grid=grid,
                )
                self.assertEqual(res_tri, res_dense)