def fit(self, X, y):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The training samples.

        y : array-like of shape (n_samples,)
            The corresponding training labels.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        # Validate the inputs X and y, and converts y to numerical classes.
        X, y = validate_data(self, X, y, ensure_min_samples=2)
        check_classification_targets(y)
        y = LabelEncoder().fit_transform(y)

        # Check the preferred dimensionality of the projected space
        if self.n_components is not None and self.n_components > X.shape[1]:
            raise ValueError(
                "The preferred dimensionality of the "
                f"projected space `n_components` ({self.n_components}) cannot "
                "be greater than the given data "
                f"dimensionality ({X.shape[1]})!"
            )
        # If warm_start is enabled, check that the inputs are consistent
        if (
            self.warm_start
            and hasattr(self, "components_")
            and self.components_.shape[1] != X.shape[1]
        ):
            raise ValueError(
                f"The new inputs dimensionality ({X.shape[1]}) does not "
                "match the input dimensionality of the "
                f"previously learned transformation ({self.components_.shape[1]})."
            )
        # Check how the linear transformation should be initialized
        init = self.init
        if isinstance(init, np.ndarray):
            init = check_array(init)
            # Assert that init.shape[1] = X.shape[1]
            if init.shape[1] != X.shape[1]:
                raise ValueError(
                    f"The input dimensionality ({init.shape[1]}) of the given "
                    "linear transformation `init` must match the "
                    f"dimensionality of the given inputs `X` ({X.shape[1]})."
                )
            # Assert that init.shape[0] <= init.shape[1]
            if init.shape[0] > init.shape[1]:
                raise ValueError(
                    f"The output dimensionality ({init.shape[0]}) of the given "
                    "linear transformation `init` cannot be "
                    f"greater than its input dimensionality ({init.shape[1]})."
                )
            # Assert that self.n_components = init.shape[0]
            if self.n_components is not None and self.n_components != init.shape[0]:
                raise ValueError(
                    "The preferred dimensionality of the "
                    f"projected space `n_components` ({self.n_components}) does"
                    " not match the output dimensionality of "
                    "the given linear transformation "
                    f"`init` ({init.shape[0]})!"
                )

        # Initialize the random generator
        self.random_state_ = check_random_state(self.random_state)

        # Measure the total training time
        t_train = time.time()

        # Compute a mask that stays fixed during optimization:
        same_class_mask = y[:, np.newaxis] == y[np.newaxis, :]
        # (n_samples, n_samples)

        # Initialize the transformation
        transformation = np.ravel(self._initialize(X, y, init))

        # Create a dictionary of parameters to be passed to the optimizer
        disp = self.verbose - 2 if self.verbose > 1 else -1
        optimizer_params = {
            "method": "L-BFGS-B",
            "fun": self._loss_grad_lbfgs,
            "args": (X, same_class_mask, -1.0),
            "jac": True,
            "x0": transformation,
            "tol": self.tol,
            "options": dict(
                maxiter=self.max_iter,
                **_get_additional_lbfgs_options_dict("disp", disp),
            ),
            "callback": self._callback,
        }

        # Call the optimizer
        self.n_iter_ = 0
        opt_result = minimize(**optimizer_params)

        # Reshape the solution found by the optimizer
        self.components_ = opt_result.x.reshape(-1, X.shape[1])

        # Stop timer
        t_train = time.time() - t_train
        if self.verbose:
            cls_name = self.__class__.__name__

            # Warn the user if the algorithm did not converge
            if not opt_result.success:
                warn(
                    "[{}] NCA did not converge: {}".format(
                        cls_name, opt_result.message
                    ),
                    ConvergenceWarning,
                )

            print("[{}] Training took {:8.2f}s.".format(cls_name, t_train))

        return self