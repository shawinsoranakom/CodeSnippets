def _gen_shape_inputs_linalg_triangular_solve(self, shape, dtype, device, well_conditioned=False):
        make_arg = partial(make_tensor, dtype=dtype, device=device)
        make_fullrank = partial(make_fullrank_matrices_with_distinct_singular_values, dtype=dtype, device=device)
        b, n, k = shape
        for left, uni, expand_a, tr_a, conj_a, expand_b, tr_b, conj_b in product((True, False), repeat=8):
            # expand means that we generate a batch of matrices with a stride of zero in the batch dimension
            if (conj_a or conj_b) and not dtype.is_complex:
                continue
            # We just expand on the batch size
            if (expand_a or expand_b) and b == 1:
                continue

            size_a = (b, n, n) if left else (b, k, k)
            size_b = (b, n, k) if not tr_b else (b, k, n)

            # If expand_a or expand_b, we'll expand them to the correct size later
            if b == 1 or expand_a:
                size_a = size_a[1:]
            if b == 1 or expand_b:
                size_b = size_b[1:]

            if well_conditioned:
                PLU = torch.linalg.lu(make_fullrank(*size_a))
                if uni:
                    # A = L from PLU
                    A = PLU[1].transpose(-2, -1).contiguous()
                else:
                    # A = U from PLU
                    A = PLU[2].contiguous()
            else:
                A = make_arg(size_a)
                A.triu_()

            diag = A.diagonal(0, -2, -1)
            if uni:
                diag.fill_(1.)
            else:
                diag[diag.abs() < 1e-6] = 1.

            B = make_arg(size_b)

            if tr_a:
                A.transpose_(-2, -1)
            if tr_b:
                B.transpose_(-2, -1)
            if conj_a:
                A = A.conj()
            if conj_b:
                B = B.conj()
            if expand_a:
                A = A.expand(b, *size_a)
            if expand_b:
                B = B.expand(b, n, k)
            yield A, B, left, not tr_a, uni