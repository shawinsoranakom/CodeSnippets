def enable_lora(
        self,
        rank,
        lora_alpha=None,
        a_initializer="he_uniform",
        b_initializer="zeros",
    ):
        if self.kernel_constraint:
            raise ValueError(
                "Lora is incompatible with kernel constraints. "
                "In order to enable lora on this layer, remove the "
                "`kernel_constraint` argument."
            )
        if not self.built:
            raise ValueError(
                "Cannot enable lora on a layer that isn't yet built."
            )
        if self.lora_enabled:
            raise ValueError(
                "lora is already enabled. This can only be done once per layer."
            )
        if self.quantization_mode == "gptq":
            raise NotImplementedError(
                "lora is not currently supported with GPTQ quantization."
            )
        self._tracker.unlock()
        # Determine the correct input dimension for the LoRA A matrix. When
        # the layer has been int4-quantized, `self._kernel` stores a *packed*
        # representation whose first dimension is `ceil(input_dim/2)`. We
        # saved the true, *unpacked* input dimension in `self._orig_input_dim`
        # during quantization. Use it if available; otherwise fall back to the
        # first dimension of `self.kernel`.
        if self.quantization_mode == "int4" and hasattr(
            self, "_orig_input_dim"
        ):
            input_dim_for_lora = self._orig_input_dim
        else:
            input_dim_for_lora = self.kernel.shape[0]

        # LoRA weights should be float32 to avoid the risk of underflow or
        # overflow during fine-tuning.
        # When deploying the model, these weights should be merged with the
        # original kernel while maintaining the original kernel's dtype.
        self.lora_kernel_a = self.add_weight(
            name="lora_kernel_a",
            shape=(input_dim_for_lora, rank),
            initializer=initializers.get(a_initializer),
            dtype="float32",
            regularizer=self.kernel_regularizer,
        )
        self.lora_kernel_b = self.add_weight(
            name="lora_kernel_b",
            shape=(rank, self.kernel.shape[1]),
            initializer=initializers.get(b_initializer),
            dtype="float32",
            regularizer=self.kernel_regularizer,
        )
        self._kernel.trainable = False
        self._tracker.lock()
        self.lora_enabled = True
        self.lora_rank = rank
        self.lora_alpha = lora_alpha if lora_alpha is not None else rank