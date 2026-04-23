def _test_print(self, device, dtype, coalesced):
        shape_sparse_dim_nnz = [
            ((), 0, 2),
            ((0,), 0, 10),
            ((2,), 0, 3),
            ((100, 3), 1, 3),
            ((100, 20, 3), 2, 0),
            ((10, 0, 3), 0, 3),
            ((10, 0, 3), 0, 0),
        ]
        printed = []
        for shape, sparse_dim, nnz in shape_sparse_dim_nnz:
            indices_shape = torch.Size((sparse_dim, nnz))
            values_shape = torch.Size((nnz,) + shape[sparse_dim:])
            printed.append(f"# shape: {torch.Size(shape)}")
            printed.append(f"# nnz: {nnz}")
            printed.append(f"# sparse_dim: {sparse_dim}")
            printed.append(f"# indices shape: {indices_shape}")
            printed.append(f"# values shape: {values_shape}")

            indices = torch.arange(indices_shape.numel(), dtype=self.index_tensor(0).dtype,
                                   device=device).view(indices_shape)
            for d in range(sparse_dim):
                indices[d].clamp_(max=(shape[d] - 1))  # make it valid index
            if not coalesced and indices.numel() > 0:
                indices[:, -1] = indices[:, 0]  # make it uncoalesced
            values_numel = values_shape.numel()
            values = torch.arange(values_numel, dtype=dtype,
                                  device=device).view(values_shape).div_(values_numel / 2.)
            sp_tensor = self.sparse_tensor(indices, values, shape, dtype=dtype, device=device)

            dtypes = [torch.int32]
            if values.dtype == torch.double:
                dtypes.append(torch.float)
            else:
                dtypes.append(highest_precision_float(values.device))
            for dtype in dtypes:
                printed.append(f"########## {dtype} ##########")
                x = sp_tensor.detach().to(dtype)
                printed.append("# sparse tensor")
                printed.append(str(x))
                if x.dtype.is_floating_point:
                    printed.append("# after requires_grad_")
                    printed.append(str(x.requires_grad_()))
                    printed.append("# after addition")
                    printed.append(str(x + x))
                printed.append("# _indices")
                printed.append(str(x._indices()))
                printed.append("# _values")
                printed.append(str(x._values()))
            printed.append('')
        self.assertExpected('\n'.join(printed))