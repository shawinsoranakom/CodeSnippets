def test_generate_simple_inputs(self):
        layouts = [torch.strided, torch.sparse_coo, torch.sparse_csr, torch.sparse_csc, torch.sparse_bsr, torch.sparse_bsc]

        tested_combinations = set()
        for tensors in zip(*map(self.generate_simple_inputs, layouts)):
            for i, t in enumerate(tensors):
                self.assertEqual(t.layout, layouts[i])

                # all layouts must produce semantically the same tensors
                self.assertEqual(t, tensors[0])

                if t.layout is torch.strided:
                    is_hybrid = None
                else:
                    is_hybrid = t.dense_dim() > 0
                if t.layout in {torch.sparse_csr, torch.sparse_bsr}:
                    is_batch = t.crow_indices().ndim > 1
                elif t.layout in {torch.sparse_csc, torch.sparse_bsc}:
                    is_batch = t.ccol_indices().ndim > 1
                else:
                    is_batch = None
                if t.layout in {torch.sparse_bsr, torch.sparse_bsc}:
                    blocksize = t.values().shape[1:3]
                    nontrivial_blocksize = 1 not in blocksize
                else:
                    nontrivial_blocksize = None
                if t.layout in {torch.sparse_csr, torch.sparse_bsr}:
                    contiguous_indices = t.crow_indices().is_contiguous() and t.col_indices().is_contiguous()
                    contiguous_values = t.values().is_contiguous()
                elif t.layout in {torch.sparse_csc, torch.sparse_bsc}:
                    contiguous_indices = t.ccol_indices().is_contiguous() and t.row_indices().is_contiguous()
                    contiguous_values = t.values().is_contiguous()
                elif t.layout is torch.sparse_coo:
                    contiguous_indices = t._indices().is_contiguous()
                    contiguous_values = t._values().is_contiguous()
                else:
                    contiguous_indices = None
                    contiguous_values = t.is_contiguous()

                tested_combinations.add((t.layout, is_hybrid, is_batch, nontrivial_blocksize,
                                         contiguous_indices, contiguous_values))

        # Ensure that the inputs generation covers all layout,
        # non-hybrid/hybrid, non-batch/batch, and contiguity
        # combinations:
        untested_combinations = set()
        for layout in layouts:
            for is_hybrid in [False, True]:
                if layout is torch.strided:
                    is_hybrid = None
                for is_batch in [False, True]:
                    if layout in {torch.sparse_coo, torch.strided}:
                        is_batch = None
                    for nontrivial_blocksize in [False, True]:
                        if layout not in {torch.sparse_bsr, torch.sparse_bsc}:
                            nontrivial_blocksize = None
                        for contiguous_indices in [False, True]:
                            if layout is torch.strided:
                                contiguous_indices = None
                            elif not is_batch:
                                # indices are contiguous per-patch
                                contiguous_indices = True
                            for contiguous_values in [False, True]:
                                key = (layout, is_hybrid, is_batch, nontrivial_blocksize,
                                       contiguous_indices, contiguous_values)
                                if key not in tested_combinations:
                                    untested_combinations.add(
                                        f'layout={layout}, is_hybrid={is_hybrid}, is_batch={is_batch},'
                                        f' nontrivial_blocksize={nontrivial_blocksize},'
                                        f' contiguous_indices{contiguous_indices}, contiguous_values={contiguous_values}')
        if untested_combinations:
            raise AssertionError(f"untested combinations: {untested_combinations}")