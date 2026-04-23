def __init__(
        self,
        call_fn,
        init_fn=None,
        params=None,
        state=None,
        seed=None,
        native_serialization_platforms=None,
        **kwargs,
    ):
        if backend.backend() not in ["jax", "tensorflow"]:
            raise ValueError(
                f"{self.__class__.__name__} is only supported with the JAX or"
                f" Tensorflow backend. Current backend: {backend.backend()}"
            )

        super().__init__(**kwargs)
        self.call_fn = call_fn
        self.init_fn = init_fn
        self.tracked_params = self._create_variables(params, trainable=True)
        self.tracked_state = self._create_variables(state, trainable=False)
        if self.params is not None or self.state is not None:
            self._build_at_init()

        self.call_fn_arguments = self._validate_signature(
            call_fn,
            "call_fn",
            {"params", "state", "rng", "inputs", "training"},
            {"inputs"},
        )
        self.call_fn_has_params = "params" in self.call_fn_arguments
        self.call_fn_has_state = "state" in self.call_fn_arguments
        call_fn_has_rng = "rng" in self.call_fn_arguments

        if call_fn_has_rng:
            self.seed_generator = backend.random.SeedGenerator(seed)
        else:
            self.seed_generator = None

        if (
            init_fn is None
            and params is None
            and state is None
            and (self.call_fn_has_params or self.call_fn_has_state)
        ):
            raise ValueError(
                "`init_fn`, `params` and `state` cannot all be `None` when "
                "`call_fn` takes a `params` or a `state` argument."
            )

        if init_fn:
            self.init_fn_arguments = self._validate_signature(
                init_fn, "init_fn", {"rng", "inputs", "training"}, {"inputs"}
            )

        # Attributes for jax2tf functions
        self.jax2tf_training_false_fn = None
        self.jax2tf_training_true_fn = None
        self.jax2tf_native_serialization_platforms = (
            native_serialization_platforms
        )