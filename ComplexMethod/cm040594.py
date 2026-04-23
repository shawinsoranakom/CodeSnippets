def __init__(
        self,
        num_thresholds=200,
        curve="ROC",
        summation_method="interpolation",
        name=None,
        dtype=None,
        thresholds=None,
        multi_label=False,
        num_labels=None,
        label_weights=None,
        from_logits=False,
    ):
        # Metric should be maximized during optimization.
        self._direction = "up"

        # Validate configurations.
        if isinstance(curve, metrics_utils.AUCCurve) and curve not in list(
            metrics_utils.AUCCurve
        ):
            raise ValueError(
                f'Invalid `curve` argument value "{curve}". '
                f"Expected one of: {list(metrics_utils.AUCCurve)}"
            )
        if isinstance(
            summation_method, metrics_utils.AUCSummationMethod
        ) and summation_method not in list(metrics_utils.AUCSummationMethod):
            raise ValueError(
                "Invalid `summation_method` "
                f'argument value "{summation_method}". '
                f"Expected one of: {list(metrics_utils.AUCSummationMethod)}"
            )

        # Update properties.
        self._init_from_thresholds = thresholds is not None
        if thresholds is not None:
            # If specified, use the supplied thresholds.
            self.num_thresholds = len(thresholds) + 2
            thresholds = sorted(thresholds)
            self._thresholds_distributed_evenly = (
                metrics_utils.is_evenly_distributed_thresholds(
                    np.array([0.0] + thresholds + [1.0])
                )
            )
        else:
            if num_thresholds <= 1:
                raise ValueError(
                    "Argument `num_thresholds` must be an integer > 1. "
                    f"Received: num_thresholds={num_thresholds}"
                )

            # Otherwise, linearly interpolate (num_thresholds - 2) thresholds in
            # (0, 1).
            self.num_thresholds = num_thresholds
            thresholds = [
                (i + 1) * 1.0 / (num_thresholds - 1)
                for i in range(num_thresholds - 2)
            ]
            self._thresholds_distributed_evenly = True

        # Add an endpoint "threshold" below zero and above one for either
        # threshold method to account for floating point imprecisions.
        self._thresholds = np.array(
            [0.0 - backend.epsilon()] + thresholds + [1.0 + backend.epsilon()]
        )

        if isinstance(curve, metrics_utils.AUCCurve):
            self.curve = curve
        else:
            self.curve = metrics_utils.AUCCurve.from_str(curve)
        if isinstance(summation_method, metrics_utils.AUCSummationMethod):
            self.summation_method = summation_method
        else:
            self.summation_method = metrics_utils.AUCSummationMethod.from_str(
                summation_method
            )
        super().__init__(name=name, dtype=dtype)

        # Handle multilabel arguments.
        self.multi_label = multi_label
        self.num_labels = num_labels
        if label_weights is not None:
            label_weights = ops.array(label_weights, dtype=self.dtype)
            self.label_weights = label_weights

        else:
            self.label_weights = None

        self._from_logits = from_logits

        self._built = False
        if self.multi_label:
            if num_labels:
                shape = [None, num_labels]
                self._build(shape)
        else:
            if num_labels:
                raise ValueError(
                    "`num_labels` is needed only when `multi_label` is True."
                )
            self._build(None)