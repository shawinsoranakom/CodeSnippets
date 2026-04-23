def genSparseCompressedTensor(self, size, nnz, *, layout, device, dtype, index_dtype, blocksize=(), dense_dims=0):
        from operator import mul
        from functools import reduce
        sparse_dim = 2
        if not (all(size[d] > 0 for d in range(len(size))) or nnz == 0):
            raise AssertionError(f"invalid arguments: size={size}, nnz={nnz}")
        if len(size) < sparse_dim:
            raise AssertionError(f"expected len(size) >= {sparse_dim}, got {len(size)}")
        if blocksize:
            if len(blocksize) != 2:
                raise AssertionError(f"expected len(blocksize) == 2, got size={size}, blocksize={blocksize}")
            if size[-2 - dense_dims] % blocksize[0] != 0:
                raise AssertionError(
                    f"size[-2 - dense_dims] must be divisible by blocksize[0]: size={size}, blocksize={blocksize}"
                )
            if size[-1 - dense_dims] % blocksize[1] != 0:
                raise AssertionError(
                    f"size[-1 - dense_dims] must be divisible by blocksize[1]: size={size}, blocksize={blocksize}"
                )
            blocksize0, blocksize1 = blocksize
        else:
            blocksize0 = blocksize1 = 1

        size = tuple(size)
        dense_size = size[(len(size) - dense_dims):]

        def random_sparse_compressed(n_compressed_dims, n_plain_dims, nnz):
            compressed_indices = self._make_crow_indices(n_compressed_dims, n_plain_dims, nnz, device=device, dtype=index_dtype)
            plain_indices = torch.zeros(nnz, dtype=index_dtype, device=device)
            for i in range(n_compressed_dims):
                count = compressed_indices[i + 1] - compressed_indices[i]
                plain_indices[compressed_indices[i]:compressed_indices[i + 1]], _ = torch.sort(
                    torch.randperm(n_plain_dims, dtype=index_dtype, device=device)[:count])
            low = -1 if dtype != torch.uint8 else 0
            high = 1 if dtype != torch.uint8 else 2
            values = make_tensor((nnz,) + blocksize + dense_size, device=device, dtype=dtype, low=low, high=high)
            return values, compressed_indices, plain_indices

        batch_shape = size[:-2 - dense_dims]
        n_batch = reduce(mul, batch_shape, 1)

        if layout in {torch.sparse_csr, torch.sparse_bsr}:
            n_compressed_dims, n_plain_dims = size[-2 - dense_dims] // blocksize0, size[-1 - dense_dims] // blocksize1
        else:
            n_compressed_dims, n_plain_dims = size[-1 - dense_dims] // blocksize1, size[-2 - dense_dims] // blocksize0
        blocknnz = nnz // (blocksize0 * blocksize1)
        sparse_tensors = [random_sparse_compressed(n_compressed_dims, n_plain_dims, blocknnz) for _ in range(n_batch)]
        sparse_tensors_it = map(list, zip(*sparse_tensors, strict=True))

        values = torch.stack(next(sparse_tensors_it)).reshape(*batch_shape, blocknnz, *blocksize, *dense_size)
        compressed_indices = torch.stack(next(sparse_tensors_it)).reshape(*batch_shape, -1)
        plain_indices = torch.stack(next(sparse_tensors_it)).reshape(*batch_shape, -1)
        return torch.sparse_compressed_tensor(compressed_indices, plain_indices,
                                              values, size=size, dtype=dtype, layout=layout, device=device)