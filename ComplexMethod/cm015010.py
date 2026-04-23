def run_test(shape, *, symmetric=False):
            from torch.testing._internal.common_utils import random_symmetric_matrix

            if not dtype.is_complex and symmetric:
                # for symmetric real-valued inputs eigenvalues and eigenvectors have imaginary part equal to zero
                a = random_symmetric_matrix(shape[-1], *shape[:-2], dtype=dtype, device=device)
            else:
                a = make_tensor(shape, dtype=dtype, device=device)

            actual = torch.linalg.eig(a)

            # set tolerance for correctness check
            if dtype in [torch.float32, torch.complex64]:
                atol = 1e-3  # CuSolver gives less accurate results for single precision (1-2 larger than OOM NumPy)
            else:
                atol = 1e-13  # Same OOM for NumPy

            # check correctness using eigendecomposition identity
            w, v = actual
            a = a.to(v.dtype)

            if a.numel() == 0 and v.numel() == 0 and w.numel() == 0:
                pass
            elif a.numel() == 0 or v.numel() == 0 or w.numel() == 0:
                raise RuntimeError("eig returned empty tensors unexpectedly")

            self.assertEqual(a @ v, v * w.unsqueeze(-2), atol=atol, rtol=0)

            # calculate eigenvalues only and check all are returned
            w_only = torch.linalg.eigvals(a)
            self.assertEqual(w_only.shape, w.shape)

            if a.numel() != 0:
                # calculate distance matrix and find best matches
                match_min_diff, match_idx = (w.unsqueeze(-1) - w_only.unsqueeze(-2)).abs().min(-1)

                # check eigenvalues match within tolerance
                self.assertEqual(match_min_diff, torch.zeros_like(match_min_diff),
                                 atol=atol, rtol=0, msg="eigenvalues do not match within tolerance!")
                # check all eigenvalues have unique matches
                self.assertEqual(match_idx.sort(-1).values,
                                 torch.arange(0, match_idx.shape[-1]).expand_as(match_idx),
                                 atol=0, rtol=0, msg="some eigenvalues have multiple matches!")