def test_print(self, layout, device):
        compressed_indices_mth, plain_indices_mth = sparse_compressed_indices_methods[layout]
        printed = []
        for enable_hybrid in [False, True]:
            # using local patterns for test_print stability
            patterns = [
                # 2 x 3 batch of 3 x 2 tensors, trivial blocksize, non-hybrid/hybrid:
                ([[[[1, 2, 0],
                    [1, 0, 3]],
                   [[1, 2, 3],
                    [1, 0, 0]],
                   [[1, 0, 0],
                    [1, 2, 3]]],
                  [[[0, 2, 0],
                    [1, 2, 3]],
                   [[1, 0, 3],
                    [1, 2, 0]],
                   [[1, 2, 3],
                    [0, 2, 0]]]], [(2, 1)], [(), (4,)] if enable_hybrid else [()]),
                # tensor with non-trivial blocksize, non-hybrid/hybrid:
                ([[0, 1, 0, 2, 0, 2],
                  [0, 1, 0, 0, 2, 0],
                  [3, 3, 3, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0],
                  [0, 5, 0, 6, 6, 6],
                  [5, 0, 5, 6, 6, 6],
                  [0, 0, 0, 0, 8, 8],
                  [7, 7, 7, 0, 8, 8]], [(2, 3)], [(), (4, 2)] if enable_hybrid else [()]),
            ]
            for index_dtype in [torch.int32, torch.int64]:
                for dtype in [torch.float32, torch.float64]:
                    for (compressed_indices, plain_indices, values), kwargs in self.generate_simple_inputs(
                            layout, device=device, dtype=dtype, index_dtype=index_dtype, enable_hybrid=enable_hybrid,
                            enable_non_contiguous_indices=False, enable_non_contiguous_values=False,
                            enable_zero_sized=False, output_tensor=False, patterns=patterns):
                        size = tuple(kwargs['size'])
                        block_ndim = 2 if layout in {torch.sparse_bsr, torch.sparse_bsc} else 0
                        base_ndim = 2
                        batch_ndim = compressed_indices.dim() - 1
                        dense_ndim = values.dim() - batch_ndim - block_ndim - 1
                        if enable_hybrid and dense_ndim == 0:
                            # non-hybrid cases are covered by the enable_hybrid==False loop
                            continue
                        batchsize = size[:batch_ndim]
                        basesize = size[batch_ndim:batch_ndim + base_ndim]
                        densesize = size[batch_ndim + base_ndim:]
                        if len(densesize) != dense_ndim:
                            raise AssertionError(f"expected len(densesize) == {dense_ndim}, got {len(densesize)}")
                        printed.append(f"########## {dtype}/{index_dtype}/size={batchsize}+{basesize}+{densesize} ##########")
                        x = torch.sparse_compressed_tensor(compressed_indices,
                                                           plain_indices,
                                                           values, size, dtype=dtype, layout=layout, device=device)
                        printed.append("# sparse tensor")
                        printed.append(str(x))
                        printed.append(f"# _{compressed_indices_mth.__name__}")
                        printed.append(str(compressed_indices_mth(x)))
                        printed.append(f"# _{plain_indices_mth.__name__}")
                        printed.append(str(plain_indices_mth(x)))
                        printed.append("# _values")
                        printed.append(str(x.values()))
                        printed.append('')
                    printed.append('')
        orig_maxDiff = self.maxDiff
        self.maxDiff = None
        try:
            self.assertExpected('\n'.join(printed))
            self.maxDiff = orig_maxDiff
        except Exception:
            self.maxDiff = orig_maxDiff
            raise