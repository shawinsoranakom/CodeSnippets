def test_linalg(device="cpu") -> None:
    print(f"Testing smoke_test_linalg on {device}")
    A = torch.randn(5, 3, device=device)
    U, S, Vh = torch.linalg.svd(A, full_matrices=False)
    if not (
        U.shape == A.shape
        and S.shape == torch.Size([3])
        and Vh.shape == torch.Size([3, 3])
    ):
        raise AssertionError(
            f"SVD shapes mismatch: U.shape={U.shape}, S.shape={S.shape}, Vh.shape={Vh.shape}"
        )
    torch.dist(A, U @ torch.diag(S) @ Vh)

    U, S, Vh = torch.linalg.svd(A)
    if not (
        U.shape == torch.Size([5, 5])
        and S.shape == torch.Size([3])
        and Vh.shape == torch.Size([3, 3])
    ):
        raise AssertionError(
            f"SVD full_matrices shapes mismatch: U.shape={U.shape}, S.shape={S.shape}, Vh.shape={Vh.shape}"
        )
    torch.dist(A, U[:, :3] @ torch.diag(S) @ Vh)

    A = torch.randn(7, 5, 3, device=device)
    U, S, Vh = torch.linalg.svd(A, full_matrices=False)
    torch.dist(A, U @ torch.diag_embed(S) @ Vh)

    if device == "cuda":
        supported_dtypes = [torch.float32, torch.float64]
        for dtype in supported_dtypes:
            print(f"Testing smoke_test_linalg with cuda for {dtype}")
            A = torch.randn(20, 16, 50, 100, device=device, dtype=dtype)
            torch.linalg.svd(A)