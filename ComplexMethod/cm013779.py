def forward(self, X: torch.Tensor) -> torch.Tensor:
        n, k = X.size(-2), X.size(-1)
        transposed = n < k
        if transposed:
            X = X.mT
            n, k = k, n
        # Here n > k and X is a tall matrix
        if (
            self.orthogonal_map == _OrthMaps.matrix_exp
            or self.orthogonal_map == _OrthMaps.cayley
        ):
            # We just need n x k - k(k-1)/2 parameters
            X = X.tril()
            if n != k:
                # Embed into a square matrix
                X = torch.cat(
                    [X, X.new_zeros(n, n - k).expand(*X.shape[:-2], -1, -1)], dim=-1
                )
            A = X - X.mH
            # A is skew-symmetric (or skew-hermitian)
            if self.orthogonal_map == _OrthMaps.matrix_exp:
                Q = torch.matrix_exp(A)
            elif self.orthogonal_map == _OrthMaps.cayley:
                # Computes the Cayley retraction (I+A/2)(I-A/2)^{-1}
                Id = torch.eye(n, dtype=A.dtype, device=A.device)
                Q = torch.linalg.solve(
                    torch.add(Id, A, alpha=-0.5), torch.add(Id, A, alpha=0.5)
                )
            # Q is now orthogonal (or unitary) of size (..., n, n)
            if n != k:
                # pyrefly: ignore [unbound-name]
                Q = Q[..., :k]
            # Q is now the size of the X (albeit perhaps transposed)
        else:
            # X is real here, as we do not support householder with complex numbers
            A = X.tril(diagonal=-1)
            tau = 2.0 / (1.0 + (A * A).sum(dim=-2))
            Q = torch.linalg.householder_product(A, tau)
            # The diagonal of X is 1's and -1's
            # We do not want to differentiate through this or update the diagonal of X hence the casting
            Q = Q * X.diagonal(dim1=-2, dim2=-1).int().unsqueeze(-2)

        if hasattr(self, "base"):
            # pyrefly: ignore [unbound-name]
            Q = self.base @ Q
        if transposed:
            # pyrefly: ignore [unbound-name]
            Q = Q.mT
        return Q