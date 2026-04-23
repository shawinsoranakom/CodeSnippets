def _create_q_galore_optimizer(self, config: "QGaloreConfig", embedding_lr = None):
        """Build the Q-GaLore optimizer from a QGaloreConfig."""
        from unsloth.optimizers.q_galore_adamw import (
            QGaLoreAdamW8bit,
            make_q_galore_param_groups,
            install_weight_quant_hooks,
        )

        lr = self.args.learning_rate
        weight_decay = self.args.weight_decay

        param_groups = make_q_galore_param_groups(
            self.model,
            lr = lr,
            weight_decay = weight_decay,
            rank = config.rank,
            update_proj_gap = config.update_proj_gap,
            scale = config.scale,
            proj_quant = config.proj_quant,
            proj_quant_group_size = config.proj_quant_group_size,
            proj_quant_n_bit = config.proj_quant_n_bit,
            weight_quant = config.weight_quant,
            stochastic_round = config.stochastic_round,
            weight_group_size = config.weight_group_size,
            cos_threshold = config.cos_threshold,
            gamma_proj = config.gamma_proj,
            queue_size = config.queue_size,
            target_modules = config.target_modules,
        )

        # --- Split embedding params with custom LR (Fix #2) ---
        if embedding_lr is not None:
            # Build a fast param->name lookup (O(N) instead of O(N*M))
            param_to_name = {id(p): name for name, p in self.model.named_parameters()}

            new_groups = []
            for group in param_groups:
                if "rank" in group:
                    # GaLore group — keep as-is (embeddings are never in here)
                    new_groups.append(group)
                    continue
                # Non-GaLore group: split out embedding params
                embed_params = []
                other_params = []
                for p in group["params"]:
                    # Check if this param belongs to a modules_to_save embedding
                    name = param_to_name.get(id(p))
                    if name and name.endswith("modules_to_save.default.weight"):
                        partial_name = name[: -len(".modules_to_save.default.weight")]
                        partial_name = partial_name[partial_name.rfind(".") + 1 :]
                        print(
                            f"Unsloth: Setting lr = {embedding_lr:.2e} instead of {lr:.2e} for {partial_name}."
                        )
                        embed_params.append(p)
                    else:
                        other_params.append(p)
                if other_params:
                    other_group = dict(group)
                    other_group["params"] = other_params
                    new_groups.append(other_group)
                if embed_params:
                    embed_group = dict(group)
                    embed_group["params"] = embed_params
                    embed_group["lr"] = embedding_lr
                    new_groups.append(embed_group)
            param_groups = new_groups

        # --- Forward optimizer hyperparameters (Fix #3) ---
        self.optimizer = QGaLoreAdamW8bit(
            param_groups,
            lr = lr,
            weight_decay = weight_decay,
            betas = (self.args.adam_beta1, self.args.adam_beta2),
            eps = self.args.adam_epsilon,
        )

        # Initialize INT8 weight quantization if enabled
        if config.weight_quant:
            QGaLoreAdamW8bit.init_weight_quantization(
                self.model,
                param_groups,
                group_size = config.weight_group_size,
                stochastic = config.stochastic_round,
            )
            # Forward pre-hooks dequantize INT8 weights to float before each
            # forward pass, allowing the optimizer to free float weight memory
            # between steps.
            install_weight_quant_hooks(self.model)

        n_galore = sum(len(g["params"]) for g in param_groups if "rank" in g)
        n_other = sum(len(g["params"]) for g in param_groups if "rank" not in g)
        print(
            f"🦥 Unsloth: Q-GaLore enabled — "
            f"{n_galore} GaLore params (rank={config.rank}), "
            f"{n_other} standard params."
        )

        return self.optimizer