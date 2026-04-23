def gradient_hessian(
        self,
        y_true,
        raw_prediction,
        sample_weight=None,
        gradient_out=None,
        hessian_out=None,
        n_threads=1,
    ):
        """Compute gradient and hessian of loss w.r.t raw_prediction.

        Parameters
        ----------
        y_true : C-contiguous array of shape (n_samples,)
            Observed, true target values.
        raw_prediction : C-contiguous array of shape (n_samples,) or array of \
            shape (n_samples, n_classes)
            Raw prediction values (in link space).
        sample_weight : None or C-contiguous array of shape (n_samples,)
            Sample weights.
        gradient_out : None or C-contiguous array of shape (n_samples,) or array \
            of shape (n_samples, n_classes)
            A location into which the gradient is stored. If None, a new array
            might be created.
        hessian_out : None or C-contiguous array of shape (n_samples,) or array \
            of shape (n_samples, n_classes)
            A location into which the hessian is stored. If None, a new array
            might be created.
        n_threads : int, default=1
            Might use openmp thread parallelism.

        Returns
        -------
        gradient : arrays of shape (n_samples,) or (n_samples, n_classes)
            Element-wise gradients.

        hessian : arrays of shape (n_samples,) or (n_samples, n_classes)
            Element-wise hessians.
        """
        if gradient_out is None:
            if hessian_out is None:
                gradient_out = np.empty_like(raw_prediction)
                hessian_out = np.empty_like(raw_prediction)
            else:
                gradient_out = np.empty_like(hessian_out)
        elif hessian_out is None:
            hessian_out = np.empty_like(gradient_out)

        # Be graceful to shape (n_samples, 1) -> (n_samples,)
        if raw_prediction.ndim == 2 and raw_prediction.shape[1] == 1:
            raw_prediction = raw_prediction.squeeze(1)
        if gradient_out.ndim == 2 and gradient_out.shape[1] == 1:
            gradient_out = gradient_out.squeeze(1)
        if hessian_out.ndim == 2 and hessian_out.shape[1] == 1:
            hessian_out = hessian_out.squeeze(1)

        self.closs.gradient_hessian(
            y_true=y_true,
            raw_prediction=raw_prediction,
            sample_weight=sample_weight,
            gradient_out=gradient_out,
            hessian_out=hessian_out,
            n_threads=n_threads,
        )
        return gradient_out, hessian_out