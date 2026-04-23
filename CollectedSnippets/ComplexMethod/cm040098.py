def __init__(
        self,
        axis=-1,
        momentum=0.99,
        epsilon=1e-3,
        center=True,
        scale=True,
        beta_initializer="zeros",
        gamma_initializer="ones",
        moving_mean_initializer="zeros",
        moving_variance_initializer="ones",
        beta_regularizer=None,
        gamma_regularizer=None,
        beta_constraint=None,
        gamma_constraint=None,
        renorm=False,
        renorm_clipping=None,
        renorm_momentum=0.99,
        synchronized=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.axis = int(axis)

        if synchronized and backend.backend() != "tensorflow":
            raise ValueError(
                "Argument synchronized=True is only supported "
                "with the TensorFlow backend."
            )
        self.synchronized = synchronized

        self.momentum = float(momentum)
        self.epsilon = float(epsilon)
        self.center = center
        self.scale = scale
        self.beta_initializer = initializers.get(beta_initializer)
        self.gamma_initializer = initializers.get(gamma_initializer)
        self.moving_mean_initializer = initializers.get(moving_mean_initializer)
        self.moving_variance_initializer = initializers.get(
            moving_variance_initializer
        )
        self.beta_regularizer = regularizers.get(beta_regularizer)
        self.gamma_regularizer = regularizers.get(gamma_regularizer)
        self.beta_constraint = constraints.get(beta_constraint)
        self.gamma_constraint = constraints.get(gamma_constraint)
        self.supports_masking = True

        self.renorm = renorm
        if renorm:
            renorm_clipping = renorm_clipping or {}
            keys = ["rmax", "rmin", "dmax"]
            if set(renorm_clipping) - set(keys):
                raise ValueError(
                    "Received invalid keys for `renorm_clipping` argument: "
                    f"{renorm_clipping}. Supported values: {keys}."
                )
            rmax = renorm_clipping.get("rmax")
            rmin = renorm_clipping.get("rmin")
            dmax = renorm_clipping.get("dmax")

            if rmax is not None and rmin is not None and rmax < rmin:
                raise ValueError(
                    "rmax should be greater than rmin in the `renorm_clipping` "
                    "argument. Received: rmax={rmax}, rmin={rmin}."
                )
            if dmax is not None and dmax < 0:
                raise ValueError(
                    "dmax should be non-negative in the `renorm_clipping` "
                    """argument. Received: dmax={dmax}."""
                )

        self.renorm_clipping = renorm_clipping
        self.renorm_momentum = renorm_momentum

        self.gamma = None
        self.beta = None
        self.moving_mean = None
        self.moving_variance = None
        self._reduction_axes = None