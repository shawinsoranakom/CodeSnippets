def _spectral_embedding(
    adjacency,
    *,
    n_components=8,
    eigen_solver=None,
    random_state=None,
    eigen_tol="auto",
    norm_laplacian=True,
    drop_first=True,
):
    adjacency = check_symmetric(adjacency)

    if eigen_solver == "amg":
        try:
            from pyamg import aggregation, smoothed_aggregation_solver
        except ImportError as e:
            raise ValueError(
                "The eigen_solver was set to 'amg', but pyamg is not available."
            ) from e
        pyamg_supports_sparray = hasattr(aggregation.aggregation, "csr_array")

    if eigen_solver is None:
        eigen_solver = "arpack"

    n_nodes = adjacency.shape[0]
    # Whether to drop the first eigenvector
    if drop_first:
        n_components = n_components + 1

    if not _graph_is_connected(adjacency):
        warnings.warn(
            "Graph is not fully connected, spectral embedding may not work as expected."
        )

    laplacian, dd = csgraph_laplacian(
        adjacency, normed=norm_laplacian, return_diag=True
    )
    if eigen_solver == "arpack" or (
        eigen_solver != "lobpcg"
        and (not sparse.issparse(laplacian) or n_nodes < 5 * n_components)
    ):
        # lobpcg used with eigen_solver='amg' has bugs for low number of nodes
        # for details see the source code in scipy:
        # https://github.com/scipy/scipy/blob/v0.11.0/scipy/sparse/linalg/eigen
        # /lobpcg/lobpcg.py#L237
        # or matlab:
        # https://www.mathworks.com/matlabcentral/fileexchange/48-lobpcg-m
        laplacian = _set_diag(laplacian, 1, norm_laplacian)

        # Here we'll use shift-invert mode for fast eigenvalues
        # (see https://docs.scipy.org/doc/scipy/reference/tutorial/arpack.html
        #  for a short explanation of what this means)
        # Because the normalized Laplacian has eigenvalues between 0 and 2,
        # I - L has eigenvalues between -1 and 1.  ARPACK is most efficient
        # when finding eigenvalues of largest magnitude (keyword which='LM')
        # and when these eigenvalues are very large compared to the rest.
        # For very large, very sparse graphs, I - L can have many, many
        # eigenvalues very near 1.0.  This leads to slow convergence.  So
        # instead, we'll use ARPACK's shift-invert mode, asking for the
        # eigenvalues near 1.0.  This effectively spreads-out the spectrum
        # near 1.0 and leads to much faster convergence: potentially an
        # orders-of-magnitude speedup over simply using keyword which='LA'
        # in standard mode.
        try:
            # We are computing the opposite of the laplacian inplace so as
            # to spare a memory allocation of a possibly very large array
            tol = 0 if eigen_tol == "auto" else eigen_tol
            laplacian *= -1
            v0 = _init_arpack_v0(laplacian.shape[0], random_state)
            laplacian = check_array(
                laplacian, accept_sparse="csr", accept_large_sparse=False
            )
            _, diffusion_map = eigsh(
                laplacian, k=n_components, sigma=1.0, which="LM", tol=tol, v0=v0
            )
            embedding = diffusion_map.T[n_components::-1]
            if norm_laplacian:
                # recover u = D^-1/2 x from the eigenvector output x
                embedding = embedding / dd
        except RuntimeError:
            # When submatrices are exactly singular, an LU decomposition
            # in arpack fails. We fallback to lobpcg
            eigen_solver = "lobpcg"
            # Revert the laplacian to its opposite to have lobpcg work
            laplacian *= -1

    elif eigen_solver == "amg":
        # Use AMG to get a preconditioner and speed up the eigenvalue
        # problem.
        if not sparse.issparse(laplacian):
            warnings.warn("AMG works better for sparse matrices")
        laplacian = check_array(
            laplacian, dtype=[np.float64, np.float32], accept_sparse=True
        )
        laplacian = _set_diag(laplacian, 1, norm_laplacian)

        # The Laplacian matrix is always singular, having at least one zero
        # eigenvalue, corresponding to the trivial eigenvector, which is a
        # constant. Using a singular matrix for preconditioning may result in
        # random failures in LOBPCG and is not supported by the existing
        # theory:
        #     see https://doi.org/10.1007/s10208-015-9297-1
        # Shift the Laplacian so its diagononal is not all ones. The shift
        # does change the eigenpairs however, so we'll feed the shifted
        # matrix to the solver and afterward set it back to the original.
        diag_shift = 1e-5 * _sparse_eye_array(laplacian.shape[0])
        laplacian += diag_shift
        if hasattr(sparse, "csr_array") and isinstance(laplacian, sparse.csr_array):
            # old version `pyamg` may not work with `csr_array` and new version
            # may not work with `csr_matrix`. But we need to convert to CSR.
            if pyamg_supports_sparray:
                laplacian = sparse.csr_array(laplacian)
            else:
                laplacian = sparse.csr_matrix(laplacian)

        ml = smoothed_aggregation_solver(check_array(laplacian, accept_sparse="csr"))
        laplacian -= diag_shift

        M = ml.aspreconditioner()
        # Create initial approximation X to eigenvectors
        X = random_state.standard_normal(size=(laplacian.shape[0], n_components + 1))
        X[:, 0] = dd.ravel()
        X = X.astype(laplacian.dtype)

        tol = None if eigen_tol == "auto" else eigen_tol
        _, diffusion_map = lobpcg(laplacian, X, M=M, tol=tol, largest=False)
        embedding = diffusion_map.T
        if norm_laplacian:
            # recover u = D^-1/2 x from the eigenvector output x
            embedding = embedding / dd
        if embedding.shape[0] == 1:
            raise ValueError

    if eigen_solver == "lobpcg":
        laplacian = check_array(
            laplacian, dtype=[np.float64, np.float32], accept_sparse=True
        )
        if n_nodes < 5 * n_components + 1:
            # see note above under arpack why lobpcg has problems with small
            # number of nodes
            # lobpcg will fallback to eigh, so we short circuit it
            if sparse.issparse(laplacian):
                laplacian = laplacian.toarray()
            _, diffusion_map = eigh(laplacian, check_finite=False)
            embedding = diffusion_map.T[:n_components]
            if norm_laplacian:
                # recover u = D^-1/2 x from the eigenvector output x
                embedding = embedding / dd
        else:
            laplacian = _set_diag(laplacian, 1, norm_laplacian)
            # We increase the number of eigenvectors requested, as lobpcg
            # doesn't behave well in low dimension and create initial
            # approximation X to eigenvectors
            X = random_state.standard_normal(
                size=(laplacian.shape[0], n_components + 1)
            )
            X[:, 0] = dd.ravel()
            X = X.astype(laplacian.dtype)
            tol = None if eigen_tol == "auto" else eigen_tol
            _, diffusion_map = lobpcg(
                laplacian, X, tol=tol, largest=False, maxiter=2000
            )
            embedding = diffusion_map.T[:n_components]
            if norm_laplacian:
                # recover u = D^-1/2 x from the eigenvector output x
                embedding = embedding / dd
            if embedding.shape[0] == 1:
                raise ValueError

    embedding = _deterministic_vector_sign_flip(embedding)
    if drop_first:
        return embedding[1:n_components].T
    else:
        return embedding[:n_components].T