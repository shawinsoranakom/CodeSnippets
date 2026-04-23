def gradient_hessian(
        self,
        coef,
        X,
        y,
        sample_weight=None,
        l2_reg_strength=0.0,
        n_threads=1,
        gradient_out=None,
        hessian_out=None,
        raw_prediction=None,
    ):
        """Computes gradient and hessian w.r.t. coef.

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
        gradient_out : None or ndarray of shape coef.shape
            A location into which the gradient is stored. If None, a new array
            might be created.
        hessian_out : None or ndarray of shape (n_dof, n_dof) or \
            (n_classes * n_dof, n_classes * n_dof)
            A location into which the hessian is stored. If None, a new array
            might be created.
        raw_prediction : C-contiguous array of shape (n_samples,) or array of \
            shape (n_samples, n_classes)
            Raw prediction values (in link space). If provided, these are used. If
            None, then raw_prediction = X @ coef + intercept is calculated.

        Returns
        -------
        gradient : ndarray of shape coef.shape
             The gradient of the loss.

        hessian : ndarray of shape (n_dof, n_dof) or \
            (n_classes, n_dof, n_dof, n_classes)
            Hessian matrix.

        hessian_warning : bool
            True if pointwise hessian has more than 25% of its elements non-positive.
        """
        (n_samples, n_features), n_classes = X.shape, self.base_loss.n_classes
        n_dof = n_features + int(self.fit_intercept)
        if raw_prediction is None:
            weights, intercept, raw_prediction = self.weight_intercept_raw(coef, X)
        else:
            weights, intercept = self.weight_intercept(coef)
        sw_sum = n_samples if sample_weight is None else np.sum(sample_weight)

        # Allocate gradient.
        if gradient_out is None:
            grad = np.empty_like(coef, dtype=weights.dtype, order="F")
        elif gradient_out.shape != coef.shape:
            raise ValueError(
                f"gradient_out is required to have shape coef.shape = {coef.shape}; "
                f"got {gradient_out.shape}."
            )
        elif self.base_loss.is_multiclass and not gradient_out.flags.f_contiguous:
            raise ValueError("gradient_out must be F-contiguous.")
        else:
            grad = gradient_out
        # Allocate hessian.
        n = coef.size  # for multinomial this equals n_dof * n_classes
        if hessian_out is None:
            hess = np.empty((n, n), dtype=weights.dtype)
        elif hessian_out.shape != (n, n):
            raise ValueError(
                f"hessian_out is required to have shape ({n, n}); got "
                f"{hessian_out.shape=}."
            )
        elif self.base_loss.is_multiclass and (
            not hessian_out.flags.c_contiguous and not hessian_out.flags.f_contiguous
        ):
            raise ValueError("hessian_out must be contiguous.")
        else:
            hess = hessian_out

        if not self.base_loss.is_multiclass:
            grad_pointwise, hess_pointwise = self.base_loss.gradient_hessian(
                y_true=y,
                raw_prediction=raw_prediction,
                sample_weight=sample_weight,
                n_threads=n_threads,
            )
            grad_pointwise /= sw_sum
            hess_pointwise /= sw_sum

            # For non-canonical link functions and far away from the optimum, the
            # pointwise hessian can be negative. We take care that 75% of the hessian
            # entries are positive.
            hessian_warning = (
                np.average(hess_pointwise <= 0, weights=sample_weight) > 0.25
            )
            hess_pointwise = np.abs(hess_pointwise)

            grad[:n_features] = X.T @ grad_pointwise + l2_reg_strength * weights
            if self.fit_intercept:
                grad[-1] = grad_pointwise.sum()

            if hessian_warning:
                # Exit early without computing the hessian.
                return grad, hess, hessian_warning

            hess[:n_features, :n_features] = sandwich_dot(X, hess_pointwise)

            if l2_reg_strength > 0:
                # The L2 penalty enters the Hessian on the diagonal only. To add those
                # terms, we use a flattened view of the array.
                order = "C" if hess.flags.c_contiguous else "F"
                hess.reshape(-1, order=order)[: (n_features * n_dof) : (n_dof + 1)] += (
                    l2_reg_strength
                )

            if self.fit_intercept:
                # With intercept included as added column to X, the hessian becomes
                # hess = (X, 1)' @ diag(h) @ (X, 1)
                #      = (X' @ diag(h) @ X, X' @ h)
                #        (           h @ X, sum(h))
                # The left upper part has already been filled, it remains to compute
                # the last row and the last column.
                Xh = X.T @ hess_pointwise
                hess[:-1, -1] = Xh
                hess[-1, :-1] = Xh
                hess[-1, -1] = hess_pointwise.sum()
        else:
            # Here we may safely assume HalfMultinomialLoss aka categorical
            # cross-entropy.
            # HalfMultinomialLoss computes only the diagonal part of the hessian, i.e.
            # diagonal in the classes. Here, we want the full hessian. Therefore, we
            # call gradient_proba.
            grad_pointwise, proba = self.base_loss.gradient_proba(
                y_true=y,
                raw_prediction=raw_prediction,
                sample_weight=sample_weight,
                n_threads=n_threads,
            )
            grad_pointwise /= sw_sum
            grad = grad.reshape((n_classes, n_dof), order="F")
            grad[:, :n_features] = grad_pointwise.T @ X + l2_reg_strength * weights
            if self.fit_intercept:
                grad[:, -1] = grad_pointwise.sum(axis=0)
            if coef.ndim == 1:
                grad = grad.ravel(order="F")

            # The full hessian matrix, i.e. not only the diagonal part, dropping most
            # indices, is given by:
            #
            #   hess = X' @ h @ X
            #
            # Here, h is a priori a 4-dimensional matrix of shape
            # (n_samples, n_samples, n_classes, n_classes). It is diagonal its first
            # two dimensions (the ones with n_samples), i.e. it is
            # effectively a 3-dimensional matrix (n_samples, n_classes, n_classes).
            #
            #   h = diag(p) - p' p
            #
            # or with indices k and l for classes
            #
            #   h_kl = p_k * delta_kl - p_k * p_l
            #
            # with p_k the (predicted) probability for class k. Only the dimension in
            # n_samples multiplies with X.
            # For 3 classes and n_samples = 1, this looks like ("@" is a bit misused
            # here):
            #
            #   hess = X' @ (h00 h10 h20) @ X
            #               (h10 h11 h12)
            #               (h20 h12 h22)
            #        = (X' @ diag(h00) @ X, X' @ diag(h10), X' @ diag(h20))
            #          (X' @ diag(h10) @ X, X' @ diag(h11), X' @ diag(h12))
            #          (X' @ diag(h20) @ X, X' @ diag(h12), X' @ diag(h22))
            #
            # Now coef of shape (n_classes * n_dof) is contiguous in n_classes.
            # Therefore, we want the hessian to follow this convention, too, i.e.
            #     hess[:n_classes, :n_classes] = (x0' @ h00 @ x0, x0' @ h10 @ x0, ..)
            #                                    (x0' @ h10 @ x0, x0' @ h11 @ x0, ..)
            #                                    (x0' @ h20 @ x0, x0' @ h12 @ x0, ..)
            # is the first feature, x0, for all classes. In our implementation, we
            # still want to take advantage of BLAS "X.T @ X". Therefore, we have some
            # index/slicing battle to fight.
            if sample_weight is not None:
                sw = sample_weight / sw_sum
            else:
                sw = 1.0 / sw_sum

            for k in range(n_classes):
                # Diagonal terms (in classes) hess_kk.
                # Note that this also writes to some of the lower triangular part.
                h = proba[:, k] * (1 - proba[:, k]) * sw
                hess[
                    k : n_classes * n_features : n_classes,
                    k : n_classes * n_features : n_classes,
                ] = sandwich_dot(X, h)
                if self.fit_intercept:
                    # See above in the non multiclass case.
                    Xh = X.T @ h
                    hess[
                        k : n_classes * n_features : n_classes,
                        n_classes * n_features + k,
                    ] = Xh
                    hess[
                        n_classes * n_features + k,
                        k : n_classes * n_features : n_classes,
                    ] = Xh
                    hess[n_classes * n_features + k, n_classes * n_features + k] = (
                        h.sum()
                    )
                # Off diagonal terms (in classes) hess_kl.
                for l in range(k + 1, n_classes):
                    # Upper triangle (in classes).
                    h = -proba[:, k] * proba[:, l] * sw
                    hess[
                        k : n_classes * n_features : n_classes,
                        l : n_classes * n_features : n_classes,
                    ] = sandwich_dot(X, h)
                    if self.fit_intercept:
                        Xh = X.T @ h
                        hess[
                            k : n_classes * n_features : n_classes,
                            n_classes * n_features + l,
                        ] = Xh
                        hess[
                            n_classes * n_features + k,
                            l : n_classes * n_features : n_classes,
                        ] = Xh
                        hess[n_classes * n_features + k, n_classes * n_features + l] = (
                            h.sum()
                        )
                    # Fill lower triangle (in classes).
                    hess[l::n_classes, k::n_classes] = hess[k::n_classes, l::n_classes]

            if l2_reg_strength > 0:
                # See above in the non multiclass case.
                order = "C" if hess.flags.c_contiguous else "F"
                hess.reshape(-1, order=order)[
                    : (n_classes**2 * n_features * n_dof) : (n_classes * n_dof + 1)
                ] += l2_reg_strength

            # The pointwise hessian is always non-negative for the multinomial loss.
            hessian_warning = False

        return grad, hess, hessian_warning