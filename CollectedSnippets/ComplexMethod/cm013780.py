def right_inverse(self, Q: torch.Tensor) -> torch.Tensor:
        if Q.shape != self.shape:
            raise ValueError(
                f"Expected a matrix or batch of matrices of shape {self.shape}. "
                f"Got a tensor of shape {Q.shape}."
            )

        Q_init = Q
        n, k = Q.size(-2), Q.size(-1)
        transpose = n < k
        if transpose:
            Q = Q.mT
            n, k = k, n

        # We always make sure to always copy Q in every path
        if not hasattr(self, "base"):
            # Note [right_inverse expm cayley]
            # If we do not have use_trivialization=True, we just implement the inverse of the forward
            # map for the Householder. To see why, think that for the Cayley map,
            # we would need to find the matrix X \in R^{n x k} such that:
            # Y = torch.cat([X.tril(), X.new_zeros(n, n - k).expand(*X.shape[:-2], -1, -1)], dim=-1)
            # A = Y - Y.mH
            # cayley(A)[:, :k]
            # gives the original tensor. It is not clear how to do this.
            # Perhaps via some algebraic manipulation involving the QR like that of
            # Corollary 2.2 in Edelman, Arias and Smith?
            if (
                self.orthogonal_map == _OrthMaps.cayley
                or self.orthogonal_map == _OrthMaps.matrix_exp
            ):
                raise NotImplementedError(
                    "It is not possible to assign to the matrix exponential "
                    "or the Cayley parametrizations when use_trivialization=False."
                )

            # If parametrization == _OrthMaps.householder, make Q orthogonal via the QR decomposition.
            # Here Q is always real because we do not support householder and complex matrices.
            # See note [Householder complex]
            A, tau = torch.geqrf(Q)
            # We want to have a decomposition X = QR with diag(R) > 0, as otherwise we could
            # decompose an orthogonal matrix Q as Q = (-Q)@(-Id), which is a valid QR decomposition
            # The diagonal of Q is the diagonal of R from the qr decomposition
            A.diagonal(dim1=-2, dim2=-1).sign_()
            # Equality with zero is ok because LAPACK returns exactly zero when it does not want
            # to use a particular reflection
            A.diagonal(dim1=-2, dim2=-1)[tau == 0.0] *= -1
            return A.mT if transpose else A
        else:
            if n == k:
                # We check whether Q is orthogonal
                if not _is_orthogonal(Q):
                    Q = _make_orthogonal(Q)
                else:  # Is orthogonal
                    Q = Q.clone()
            else:
                # Complete Q into a full n x n orthogonal matrix
                N = torch.randn(
                    *(Q.size()[:-2] + (n, n - k)), dtype=Q.dtype, device=Q.device
                )
                Q = torch.cat([Q, N], dim=-1)
                Q = _make_orthogonal(Q)
            self.base = Q

            # It is necessary to return the -Id, as we use the diagonal for the
            # Householder parametrization. Using -Id makes:
            # householder(torch.zeros(m,n)) == torch.eye(m,n)
            # Poor man's version of eye_like
            neg_Id = torch.zeros_like(Q_init)
            neg_Id.diagonal(dim1=-2, dim2=-1).fill_(-1.0)
            return neg_Id