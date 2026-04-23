def fit(self, X, y):
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=("csr", "csc", "coo"),
            accept_large_sparse=True,
            multi_output=True,
            y_numeric=True,
        )
        if self.raise_for_type == "sparse_array":
            correct_type = isinstance(X, sp.sparray)
        elif self.raise_for_type == "sparse_matrix":
            correct_type = isinstance(X, sp.spmatrix)
        if correct_type:
            if X.format == "coo":
                if X.row.dtype == "int64" or X.col.dtype == "int64":
                    raise ValueError("Estimator doesn't support 64-bit indices")
            elif X.format in ["csc", "csr"]:
                assert "int64" not in (
                    X.indices.dtype,
                    X.indptr.dtype,
                ), "Estimator doesn't support 64-bit indices"

        return self