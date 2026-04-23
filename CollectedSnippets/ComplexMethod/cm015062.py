def _to_from_layout(layout_a, layout_b, a):
            expect_error = True
            if {layout_a, layout_b} in allowed_pairwise_layouts_sets:
                expect_error = False

            # BSR -> CSR is not yet supported
            if (layout_a, layout_b) == (torch.sparse_bsr, torch.sparse_csr):
                expect_error = True
            # BSR -> CSC is not yet supported
            if (layout_a, layout_b) == (torch.sparse_bsr, torch.sparse_csc):
                expect_error = True
            # BSC -> CSR is not yet supported
            if (layout_a, layout_b) == (torch.sparse_bsc, torch.sparse_csr):
                expect_error = True
            # BSC -> CSC is not yet supported
            if (layout_a, layout_b) == (torch.sparse_bsc, torch.sparse_csc):
                expect_error = True
            # CSR -> BSR only works for non-batched inputs
            if (layout_a, layout_b) == (torch.sparse_csr, torch.sparse_bsr):
                if a.dim() > 2:
                    expect_error = True
            # CSR -> BSC only works for non-batched inputs
            if (layout_a, layout_b) == (torch.sparse_csr, torch.sparse_bsc):
                if a.dim() > 2:
                    expect_error = True
            # CSC -> BSR only works for non-batched inputs
            if (layout_a, layout_b) == (torch.sparse_csc, torch.sparse_bsr):
                if a.dim() > 2:
                    expect_error = True
            # CSC -> BSC only works for non-batched inputs
            if (layout_a, layout_b) == (torch.sparse_csc, torch.sparse_bsc):
                if a.dim() > 2:
                    expect_error = True

            blocksize_a = (1, 1) if layout_a in {torch.sparse_bsr, torch.sparse_bsc} else None
            blocksize_b = (1, 1) if layout_b in {torch.sparse_bsr, torch.sparse_bsc} else None
            b = a.to_sparse(layout=layout_a, blocksize=blocksize_a)
            if expect_error:
                with self.assertRaises(RuntimeError):
                    b.to_sparse(layout=layout_b, blocksize=blocksize_b)
            else:
                c = b.to_sparse(layout=layout_b, blocksize=blocksize_b)
                self.assertEqual(a.to_dense(), c.to_dense())

                # change of blocksize upon conversion is not yet supported.
                if b.layout in block_layouts:
                    for block_layout in block_layouts:
                        with self.assertRaisesRegex(RuntimeError,
                                                    "conversion from.*to.*with blocksize changed from.*to.*is not supported"):
                            b.to_sparse(layout=block_layout, blocksize=(3, 3))