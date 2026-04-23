def loss_gradient(
        self,
        y_true,
        raw_prediction,
        sample_weight=None,
        loss_out=None,
        gradient_out=None,
        n_threads=1,
    ):
        """Compute loss and gradient w.r.t. raw_prediction for each input.

        Parameters
        ----------
        y_true : C-contiguous array of shape (n_samples,)
            Observed, true target values.
        raw_prediction : C-contiguous array of shape (n_samples,) or array of \
            shape (n_samples, n_classes)
            Raw prediction values (in link space).
        sample_weight : None or C-contiguous array of shape (n_samples,)
            Sample weights.
        loss_out : None or C-contiguous array of shape (n_samples,)
            A location into which the loss is stored. If None, a new array
            might be created.
        gradient_out : None or C-contiguous array of shape (n_samples,) or array \
            of shape (n_samples, n_classes)
            A location into which the gradient is stored. If None, a new array
            might be created.
        n_threads : int, default=1
            Might use openmp thread parallelism.

        Returns
        -------
        loss : array of shape (n_samples,)
            Element-wise loss function.

        gradient : array of shape (n_samples,) or (n_samples, n_classes)
            Element-wise gradients.
        """
        if loss_out is None:
            if gradient_out is None:
                loss_out = np.empty_like(y_true)
                gradient_out = np.empty_like(raw_prediction)
            else:
                loss_out = np.empty_like(y_true, dtype=gradient_out.dtype)
        elif gradient_out is None:
            gradient_out = np.empty_like(raw_prediction, dtype=loss_out.dtype)

        # Be graceful to shape (n_samples, 1) -> (n_samples,)
        if raw_prediction.ndim == 2 and raw_prediction.shape[1] == 1:
            raw_prediction = raw_prediction.squeeze(1)
        if gradient_out.ndim == 2 and gradient_out.shape[1] == 1:
            gradient_out = gradient_out.squeeze(1)

        self.closs.loss_gradient(
            y_true=y_true,
            raw_prediction=raw_prediction,
            sample_weight=sample_weight,
            loss_out=loss_out,
            gradient_out=gradient_out,
            n_threads=n_threads,
        )
        return loss_out, gradient_out