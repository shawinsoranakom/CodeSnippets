def _initialize(self, y, layer_units, dtype):
        # set all attributes, allocate weights etc. for first call
        # Initialize parameters
        self.n_iter_ = 0
        self.t_ = 0
        self.n_outputs_ = y.shape[1]

        # Compute the number of layers
        self.n_layers_ = len(layer_units)

        # Output for regression
        if not is_classifier(self):
            if self.loss == "poisson":
                self.out_activation_ = "exp"
            else:
                # loss = "squared_error"
                self.out_activation_ = "identity"
        # Output for multi class
        elif self._label_binarizer.y_type_ == "multiclass":
            self.out_activation_ = "softmax"
        # Output for binary class and multi-label
        else:
            self.out_activation_ = "logistic"

        # Initialize coefficient and intercept layers
        self.coefs_ = []
        self.intercepts_ = []

        for i in range(self.n_layers_ - 1):
            coef_init, intercept_init = self._init_coef(
                layer_units[i], layer_units[i + 1], dtype
            )
            self.coefs_.append(coef_init)
            self.intercepts_.append(intercept_init)

        self._best_coefs = [c.copy() for c in self.coefs_]
        self._best_intercepts = [i.copy() for i in self.intercepts_]

        if self.solver in _STOCHASTIC_SOLVERS:
            self.loss_curve_ = []
            self._no_improvement_count = 0
            if self.early_stopping:
                self.validation_scores_ = []
                self.best_validation_score_ = -np.inf
                self.best_loss_ = None
            else:
                self.best_loss_ = np.inf
                self.validation_scores_ = None
                self.best_validation_score_ = None