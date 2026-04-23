def _get_svqb(self, U: Tensor, drop: bool, tau: float) -> Tensor:
        """Return B-orthonormal U.

        .. note:: When `drop` is `False` then `svqb` is based on the
                  Algorithm 4 from [DuerschPhD2015] that is a slight
                  modification of the corresponding algorithm
                  introduced in [StathopolousWu2002].

        Args:

          U (Tensor) : initial approximation, size is (m, n)
          drop (bool) : when True, drop columns that
                     contribution to the `span([U])` is small.
          tau (float) : positive tolerance

        Returns:

          U (Tensor) : B-orthonormal columns (:math:`U^T B U = I`), size
                       is (m, n1), where `n1 = n` if `drop` is `False,
                       otherwise `n1 <= n`.

        """
        if torch.numel(U) == 0:
            return U
        UBU = _utils.qform(self.B, U)
        d = UBU.diagonal(0, -2, -1)

        # Detect and drop exact zero columns from U. While the test
        # `abs(d) == 0` is unlikely to be True for random data, it is
        # possible to construct input data to lobpcg where it will be
        # True leading to a failure (notice the `d ** -0.5` operation
        # in the original algorithm). To prevent the failure, we drop
        # the exact zero columns here and then continue with the
        # original algorithm below.
        nz = torch.where(abs(d) != 0.0)
        if len(nz) != 1:
            raise AssertionError(f"expected nz to have length 1, got {nz}")
        if len(nz[0]) < len(d):
            U = U[:, nz[0]]
            if torch.numel(U) == 0:
                return U
            UBU = _utils.qform(self.B, U)
            d = UBU.diagonal(0, -2, -1)
            nz = torch.where(abs(d) != 0.0)
            if len(nz[0]) != len(d):
                raise AssertionError(
                    f"expected nz[0] length {len(d)}, got {len(nz[0])}"
                )

        # The original algorithm 4 from [DuerschPhD2015].
        d_col = (d**-0.5).reshape(d.shape[0], 1)
        DUBUD = (UBU * d_col) * d_col.mT
        E, Z = _utils.symeig(DUBUD)
        t = tau * abs(E).max()
        if drop:
            keep = torch.where(E > t)
            if len(keep) != 1:
                raise AssertionError(f"expected keep to have length 1, got {keep}")
            E = E[keep[0]]
            Z = Z[:, keep[0]]
            d_col = d_col[keep[0]]
        else:
            E[(torch.where(E < t))[0]] = t

        return torch.matmul(
            U * d_col.mT,
            Z * E**-0.5,
        )