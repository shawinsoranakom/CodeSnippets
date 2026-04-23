def step(self, closure = None):
        """Perform a single optimization step.

        For each parameter that has a ``rank`` key in its param group, the
        following sequence is executed:

        1. If ``weight_quant`` is set, dequantize the INT8 weight to float.
        2. Project the gradient to low-rank via the cached ``GaLoreProjector``.
        3. Perform the 8-bit Adam update in the low-rank space.
        4. Project the update back to full rank and add to saved weight.
        5. If ``weight_quant`` is set, re-quantize the weight to INT8.
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        if not self.initialized:
            self.check_overrides()
            self.to_gpu()
            self.initialized = True

        for gindex, group in enumerate(self.param_groups):
            for pindex, p in enumerate(group["params"]):
                if p.grad is None:
                    continue

                state = self.state[p]
                if "step" not in state:
                    state["step"] = 0

                has_weight_quant = self._has_weight_quant(p, group)

                # --- Dequantize weight if INT8 ---
                if has_weight_quant:
                    if p._q_scales is not None:
                        float_weight = _dequantize(
                            p._q_data,
                            p._q_scales,
                            p._q_zeros,
                            p._q_shape,
                        )
                        p.data = float_weight
                    # else: first step, weights are still float — skip dequantize

                # --- GaLore projection ---
                if "rank" in group:
                    if "projector" not in state:
                        state["projector"] = GaLoreProjector(
                            rank = group["rank"],
                            update_proj_gap = group.get("update_proj_gap", 200),
                            scale = group.get("scale", 0.25),
                            proj_type = group.get("proj_type", "std"),
                            quant = group.get("quant", False),
                            group_size = group.get("quant_group_size", -1),
                            n_bit = group.get("quant_n_bit", 4),
                            cos_threshold = group.get("cos_threshold", 0.4),
                            gamma_proj = group.get("gamma_proj", 2.0),
                            queue_size = group.get("queue_size", 5),
                        )

                    # Temporarily disable weight decay for GaLore params
                    # (we apply it manually after project-back)
                    if "weight_decay" in group and group["weight_decay"] > 0:
                        group["_wd_saved"] = group["weight_decay"]
                        group["weight_decay"] = 0

                    grad = state["projector"].project(p.grad, state["step"])

                    # Save current weight; replace p.data with zeros so
                    # the 8-bit update writes the pure weight delta.
                    p._saved_data = p.data.clone()
                    p.data = torch.zeros_like(
                        grad, dtype = p.data.dtype, device = p.data.device
                    )
                    p.grad = grad

                # --- 8-bit Adam update ---
                if "state1" not in state:
                    self.init_state(group, p, gindex, pindex)

                self.prefetch_state(p)
                self.update_step(group, p, gindex, pindex)

                # --- GaLore project-back ---
                if "rank" in group:
                    # p.data now holds the weight update in low-rank space
                    p.data = p._saved_data.add_(state["projector"].project_back(p.data))

                    # Re-apply decoupled weight decay using pre-update weights
                    if "_wd_saved" in group:
                        p.data.add_(
                            p.data,
                            alpha = -group["lr"] * group["_wd_saved"],
                        )
                        group["weight_decay"] = group["_wd_saved"]
                        del group["_wd_saved"]

                    del p._saved_data

                # --- Re-quantize weight to INT8 ---
                if has_weight_quant:
                    float_data = p.data
                    stochastic = group.get("stochastic_round", True)
                    gsize = group.get("weight_group_size", 128)
                    quant_fn = _quantize_stochastic if stochastic else _quantize
                    q, scales, zeros, shape = quant_fn(float_data, q_group_size = gsize)
                    p._q_data = q.to(p.data.device)
                    p._q_scales = scales
                    p._q_zeros = zeros
                    p._q_shape = shape
                    # Replace p.data with a scalar placeholder to free float memory.
                    # A forward pre-hook (install_weight_quant_hooks) will
                    # dequantize back to float before the next forward pass.
                    p.data = torch.empty(1, dtype = p.data.dtype, device = p.data.device)

                state["step"] += 1

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        return loss