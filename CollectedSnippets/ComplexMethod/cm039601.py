def gradient_hessian_product(
        self, coef, X, y, sample_weight=None, l2_reg_strength=0.0, n_threads=1
    ):
        """Computes gradient and hessp (hessian product function) w.r.t. coef.

        Parameters
        ----------
        coef : ndarray of shape (n_dof,), (n_classes, n_dof) or (n_classes * n_dof,)
            Coefficients of a linear model.
            If shape (n_classes * n_dof,), the classes of one feature are contiguous,
            i.e. one reconstructs the 2d-array via
            coef.reshape((n_classes, -1), order="F").
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data.
        y : contiguous array of shape (n_samples,)
            Observed, true target values.
        sample_weight : None or contiguous array of shape (n_samples,), default=None
            Sample weights.
        l2_reg_strength : float, default=0.0
            L2 regularization strength
        n_threads : int, default=1
            Number of OpenMP threads to use.

        Returns
        -------
        gradient : ndarray of shape coef.shape
             The gradient of the loss.

        hessp : callable
            Function that takes in a vector input of shape of gradient and
            and returns matrix-vector product with hessian.
        """
        (n_samples, n_features), n_classes = X.shape, self.base_loss.n_classes
        n_dof = n_features + int(self.fit_intercept)
        weights, intercept, raw_prediction = self.weight_intercept_raw(coef, X)
        sw_sum = n_samples if sample_weight is None else np.sum(sample_weight)

        if not self.base_loss.is_multiclass:
            grad_pointwise, hess_pointwise = self.base_loss.gradient_hessian(
                y_true=y,
                raw_prediction=raw_prediction,
                sample_weight=sample_weight,
                n_threads=n_threads,
            )
            grad_pointwise /= sw_sum
            hess_pointwise /= sw_sum
            grad = np.empty_like(coef, dtype=weights.dtype)
            grad[:n_features] = X.T @ grad_pointwise + l2_reg_strength * weights
            if self.fit_intercept:
                grad[-1] = grad_pointwise.sum()

            # Precompute as much as possible: hX, hX_sum and hessian_sum
            hessian_sum = hess_pointwise.sum()
            if sparse.issparse(X):
                hX = (
                    sparse.dia_array((hess_pointwise, 0), shape=(n_samples, n_samples))
                    @ X
                )
            else:
                hX = hess_pointwise[:, np.newaxis] * X

            if self.fit_intercept:
                # Calculate the double derivative with respect to intercept.
                # Note: In case hX is sparse, hX.sum is a matrix object.
                hX_sum = np.squeeze(np.asarray(hX.sum(axis=0)))
                # prevent squeezing to zero-dim array if n_features == 1
                hX_sum = np.atleast_1d(hX_sum)

            # With intercept included and l2_reg_strength = 0, hessp returns
            # res = (X, 1)' @ diag(h) @ (X, 1) @ s
            #     = (X, 1)' @ (hX @ s[:n_features], sum(h) * s[-1])
            # res[:n_features] = X' @ hX @ s[:n_features] + sum(h) * s[-1]
            # res[-1] = 1' @ hX @ s[:n_features] + sum(h) * s[-1]
            def hessp(s):
                ret = np.empty_like(s)
                if sparse.issparse(X):
                    ret[:n_features] = X.T @ (hX @ s[:n_features])
                else:
                    ret[:n_features] = np.linalg.multi_dot([X.T, hX, s[:n_features]])
                ret[:n_features] += l2_reg_strength * s[:n_features]

                if self.fit_intercept:
                    ret[:n_features] += s[-1] * hX_sum
                    ret[-1] = hX_sum @ s[:n_features] + hessian_sum * s[-1]
                return ret

        else:
            # Here we may safely assume HalfMultinomialLoss aka categorical
            # cross-entropy.
            # HalfMultinomialLoss computes only the diagonal part of the hessian, i.e.
            # diagonal in the classes. Here, we want the matrix-vector product of the
            # full hessian. Therefore, we call gradient_proba.
            grad_pointwise, proba = self.base_loss.gradient_proba(
                y_true=y,
                raw_prediction=raw_prediction,
                sample_weight=sample_weight,
                n_threads=n_threads,
            )
            grad_pointwise /= sw_sum
            grad = np.empty((n_classes, n_dof), dtype=weights.dtype, order="F")
            grad[:, :n_features] = grad_pointwise.T @ X + l2_reg_strength * weights
            if self.fit_intercept:
                grad[:, -1] = grad_pointwise.sum(axis=0)

            # Full hessian-vector product, i.e. not only the diagonal part of the
            # hessian. Derivation with some index battle for input vector s:
            #   - sample index i
            #   - feature indices j, m
            #   - class indices k, l
            #   - 1_{k=l} is one if k=l else 0
            #   - p_i_k is the (predicted) probability that sample i belongs to class k
            #     for all i: sum_k p_i_k = 1
            #   - s_l_m is input vector for class l and feature m
            #   - X' = X transposed
            #
            # Note: Hessian with dropping most indices is just:
            #       X' @ p_k (1(k=l) - p_l) @ X
            #
            # result_{k j} = sum_{i, l, m} Hessian_{i, k j, m l} * s_l_m
            #   = sum_{i, l, m} (X')_{ji} * p_i_k * (1_{k=l} - p_i_l)
            #                   * X_{im} s_l_m
            #   = sum_{i, m} (X')_{ji} * p_i_k
            #                * (X_{im} * s_k_m - sum_l p_i_l * X_{im} * s_l_m)
            #
            # See also https://github.com/scikit-learn/scikit-learn/pull/3646#discussion_r17461411
            def hessp(s):
                s = s.reshape((n_classes, -1), order="F")  # shape = (n_classes, n_dof)
                if self.fit_intercept:
                    s_intercept = s[:, -1]
                    s = s[:, :-1]  # shape = (n_classes, n_features)
                else:
                    s_intercept = 0
                tmp = X @ s.T + s_intercept  # X_{im} * s_k_m
                tmp -= (proba * tmp).sum(axis=1)[:, np.newaxis]  # - sum_l ..
                tmp *= proba  # * p_i_k
                if sample_weight is not None:
                    tmp *= sample_weight[:, np.newaxis]
                # hess_prod = empty_like(grad), but we ravel grad below and this
                # function is run after that.
                hess_prod = np.empty((n_classes, n_dof), dtype=weights.dtype, order="F")
                hess_prod[:, :n_features] = (tmp.T @ X) / sw_sum + l2_reg_strength * s
                if self.fit_intercept:
                    hess_prod[:, -1] = tmp.sum(axis=0) / sw_sum
                if coef.ndim == 1:
                    return hess_prod.ravel(order="F")
                else:
                    return hess_prod

            if coef.ndim == 1:
                return grad.ravel(order="F"), hessp

        return grad, hessp