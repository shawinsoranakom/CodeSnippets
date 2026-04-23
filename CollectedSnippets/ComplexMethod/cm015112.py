def softmax_jacobian_autograd(x, dim, log=False):
            """Return Jacobian of softmax using PyTorch autograd feature.

            x can be dense or sparse tensor.
            """
            import itertools

            if x.is_sparse:
                x = x.coalesce()

            dtype = x.dtype
            device = x.device
            shape = tuple(x.shape)
            J = torch.zeros((shape[dim],) + shape, dtype=dtype, device=device)
            for i in range(shape[dim]):
                if x.is_sparse:
                    sparse_dim = x.sparse_dim()
                    dense_dim = x.dense_dim()
                    if dim < sparse_dim:
                        ranges = []
                        for j, sz in enumerate(shape[:sparse_dim]):
                            if dim == j:
                                ranges.append([i])
                            else:
                                ranges.append(list(range(sz)))
                        indices = torch.tensor(list(itertools.product(*ranges)), dtype=torch.long, device=device).t()
                        values = torch.ones((indices.shape[1],) + shape[sparse_dim:], dtype=dtype, device=device)
                    else:
                        ranges = []
                        for sz in shape[:sparse_dim]:
                            ranges.append(list(range(sz)))
                        indices = torch.tensor(list(itertools.product(*ranges)), dtype=torch.long, device=device).t()
                        values = torch.zeros((indices.shape[1],) + shape[sparse_dim:], dtype=dtype, device=device)
                        sv = [slice(None)] * (dense_dim + 1)
                        sv[dim - sparse_dim + 1] = i
                        values[tuple(sv)] = 1
                    v = torch.sparse_coo_tensor(indices, values, shape, dtype=dtype, device=device)
                else:
                    v = torch.zeros_like(x)
                    sv = [slice(None)] * len(v.shape)
                    sv[dim] = i
                    v[tuple(sv)] = 1
                x_ = x.clone()
                x_.requires_grad_(True)

                if log:
                    if x_.is_sparse:
                        y = torch.sparse.log_softmax(x_, dim)
                    else:
                        y = F.log_softmax(x_, dim)
                else:
                    if x_.is_sparse:
                        y = torch.sparse.softmax(x_, dim)
                    else:
                        y = F.softmax(x_, dim)
                        # replace nan-s with zeros
                        y.data[y != y] = 0
                y.backward(v)
                g = x_.grad
                if not g.is_sparse:
                    # replace nan-s with zeros
                    g.data[g != g] = 0
                J[i] = g.to_dense() if g.is_sparse else g
            return J