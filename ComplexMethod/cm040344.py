def _check_sharding_consistency(
        self,
        trainable_shardings,
        non_trainable_shardings,
        optimizer_shardings,
        metrics_shardings,
    ):
        """Warn if there is a mix of local and distributed variable shardings.

        When some variables have SingleDeviceSharding (created outside the
        distribution scope) and others have mesh-aware shardings (created
        inside), passing them together as `out_shardings` to `jax.jit`
        raises ``ValueError: Received incompatible devices for jitted
        computation``. This helper detects the mismatch early and emits
        an actionable warning.
        """
        if distribution_lib.distribution() is None:
            return

        var_shard_pairs = itertools.chain(
            zip(self.trainable_variables, trainable_shardings),
            zip(self.non_trainable_variables, non_trainable_shardings),
            zip(
                (
                    self.optimizer.variables
                    if hasattr(self, "optimizer") and self.optimizer
                    else []
                ),
                optimizer_shardings,
            ),
            zip(self.metrics_variables, metrics_shardings),
        )

        first_local_var_path = None
        has_mesh = False
        for v, s in var_shard_pairs:
            if isinstance(s, jax.sharding.SingleDeviceSharding):
                if first_local_var_path is None:
                    first_local_var_path = v.path
            else:
                has_mesh = True
            # Early exit: we know there is a mix as soon as we have
            # seen at least one of each kind.
            if first_local_var_path and has_mesh:
                break

        if not (first_local_var_path and has_mesh):
            return

        warnings.warn(
            "Detected a mix of local (SingleDeviceSharding) and "
            "distributed (mesh-aware) variables. This will cause "
            "a 'ValueError: Received incompatible devices for "
            "jitted computation' when JAX tries to compile the "
            "training step.\n\n"
            f"First local variable found: {first_local_var_path!r}\n\n"
            "This typically happens when the model is built or "
            "weights are loaded before the distribution is set. "
            "To fix this, call set_distribution() before creating "
            "any Keras objects:\n\n"
            "    import keras\n"
            "    keras.distribution.set_distribution(distribution)\n"
            "    model = create_model()\n"
            "    model.compile(...)\n"
            "    model.fit(...)\n\n"
            "Alternatively, use the distribution scope context "
            "manager:\n\n"
            "    with distribution.scope():\n"
            "        model = create_model()\n"
            "        model.compile(...)\n"
            "        model.fit(...)\n",
            stacklevel=3,
        )