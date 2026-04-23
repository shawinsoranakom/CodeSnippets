def compute_loss(
        self, model, inputs, return_outputs = False, num_items_in_batch = None
    ):
        if return_outputs:
            raise ValueError("The GRPOTrainer does not support returning outputs")
        # Compute the per-token log probabilities for the model

        prompt_ids, prompt_mask = inputs["prompt_ids"], inputs["prompt_mask"]
        completion_ids, completion_mask = (
            inputs["completion_ids"],
            inputs["completion_mask"],
        )
        pixel_values, image_grid_thw = (
            inputs.get("pixel_values", None),
            inputs.get("image_grid_thw", None),
        )
        pixel_attention_mask, image_sizes = (
            inputs.get("pixel_attention_mask", None),
            inputs.get("image_sizes", None),
        )
        # Transformers 5.x needs token_type_ids/mm_token_type_ids for some vision models
        token_type_ids = inputs.get("token_type_ids", None)
        mm_token_type_ids = inputs.get("mm_token_type_ids", None)
        num_items_in_batch = inputs.get("num_items_in_batch", None)
        sampling_per_token_logps = inputs.get("sampling_per_token_logps", None)
        current_gradient_accumulation_steps = self.current_gradient_accumulation_steps
        num_processes = self.accelerator.num_processes

        input_ids = torch.cat([prompt_ids, completion_ids], dim = 1)
        bsz, qlen = input_ids.shape
        attention_mask = torch.cat([prompt_mask, completion_mask], dim = 1)
        # attention_mask = None
        logits_to_keep = completion_ids.size(
            1
        )  # we only need to compute the logits for the completion tokens
        _input_ids = input_ids
        _logits_to_keep = logits_to_keep

        get_logps_func = (
            lambda model,
            input_ids,
            attention_mask,
            logits_to_keep,
            batch_size = None,
            compute_entropy = False,
            compute_efficient = False: self._get_per_token_logps(
                model, input_ids, attention_mask, logits_to_keep, compute_efficient
            )
            if hasattr(self, "_get_per_token_logps")
            else self._get_per_token_logps_and_entropies(
                model,
                input_ids,
                attention_mask,
                logits_to_keep,
                batch_size,
                compute_entropy,
                compute_efficient,
            )[0]
        )  # logps

        per_token_logps = get_logps_func(
            model, input_ids, attention_mask, logits_to_keep, compute_efficient = True
        )
        # Compute the KL divergence between the model and the reference model
        # _prepare_inputs doesn't return reference log probs anymore. We need to calculate it ourselves.
        # https://github.com/huggingface/trl/blob/05bc43e960396581e458195b8388efe6b82cae1f/trl/trainer/grpo_trainer.py#L1328
        # if self.beta != 0.0:
        #     with torch.inference_mode(), model.disable_adapter():
        #         ref_per_token_logps = per_token_logps = get_logps_func(model, input_ids, attention_mask, logits_to_keep)
        # else:
        #     ref_per_token_logps = None
        ref_logps = inputs.get("ref_per_token_logps", None)
        # per_token_kl = torch.exp(ref_per_token_logps - per_token_logps) - (ref_per_token_logps - per_token_logps) - 1
        # x - x.detach() allows for preserving gradients from x
        advantages = inputs["advantages"]
        # per_token_loss = torch.exp(per_token_logps - per_token_logps.detach()) * advantages.unsqueeze(1)
        # per_token_loss = -(per_token_loss - self.beta * per_token_kl)
        # loss = ((per_token_loss * completion_mask).sum(dim=1) / completion_mask.sum(dim=1)).mean()
        old_logps = inputs.get("old_per_token_logps", None)

        input_ids = input_ids[:, -logits_to_keep:]

        # Get logit softcapping and logit scale
        logit_softcapping = _unsloth_get_final_logit_softcapping(model.config)  # Gemma
        logit_scale_multiply = getattr(model.config, "logit_scale", 0)  # Cohere
        if logit_scale_multiply is None:
            logit_scale_multiply = 0
        logit_scale_divide = getattr(model.config, "logits_scaling", 0)  # Granite
        if logit_scale_divide is None:
            logit_scale_divide = 0

        max_left_pad = inputs.get("max_left_pad", 0)
        if per_token_logps is not None:
            (
                loss,
                completion_length,
                mean_kl,
                delta,
                flat_is_ratio,
                coef_1,
                completion_mask,
            ) = grpo_compute_loss_slow(
                ref_logps,
                per_token_logps,
                old_logps,
                sampling_per_token_logps,
                input_ids,
                completion_mask,
                self.beta,
                advantages,
                pixel_values = pixel_values,
                image_grid_thw = image_grid_thw,
                loss_type = self.args.loss_type,
                importance_sampling_level = self.importance_sampling_level,
                epsilon_low = self.epsilon_low,
                epsilon_high = self.epsilon_high,
                max_completion_length = self.args.max_completion_length,
                delta = self.args.delta,
                temperature = self.args.temperature,
                max_left_pad = max_left_pad,
                logit_softcapping = logit_softcapping,
                logit_scale_multiply = logit_scale_multiply,
                logit_scale_divide = logit_scale_divide,
                num_items_in_batch = num_items_in_batch,
                current_gradient_accumulation_steps = current_gradient_accumulation_steps,
                num_processes = num_processes,
            )
        else:
            if hasattr(self.args, "loss_type"):
                (
                    loss,
                    completion_length,
                    mean_kl,
                    delta,
                    flat_is_ratio,
                    coef_1,
                    completion_mask,
                ) = grpo_accumulated_loss(
                    trainer = self,
                    input_ids = _input_ids,
                    pixel_values = pixel_values,
                    image_grid_thw = image_grid_thw,
                    logits_to_keep = logits_to_keep,
                    completion_mask = completion_mask,
                    advantages = advantages,
                    old_logps = old_logps,
                    ref_logps = ref_logps,
                    n_chunks = self.args.unsloth_num_chunks,
                    loss_type = self.args.loss_type,
                    importance_sampling_level = self.importance_sampling_level,
                    epsilon_low = self.epsilon_low,
                    epsilon_high = self.epsilon_high,
                    max_completion_length = self.args.max_completion_length,
                    delta = self.args.delta,
                    temperature = self.args.temperature,
                    max_left_pad = max_left_pad,
                    logit_softcapping = logit_softcapping,
                    logit_scale_multiply = logit_scale_multiply,
                    logit_scale_divide = logit_scale_divide,
                    attention_mask = attention_mask,
                    num_items_in_batch = num_items_in_batch,
                    current_gradient_accumulation_steps = current_gradient_accumulation_steps,
                    num_processes = num_processes,
                    sampling_per_token_logps = sampling_per_token_logps,
                    token_type_ids = token_type_ids,
                    mm_token_type_ids = mm_token_type_ids,
                )
            else:
                # to ensure backwards compatibility with trl 0.15.2 and maybe even 0.17
                loss, completion_length, mean_kl, coef_1, completion_mask = (
                    grpo_accumulated_loss(
                        trainer = self,
                        input_ids = _input_ids,
                        logits_to_keep = logits_to_keep,
                        completion_mask = completion_mask,
                        advantages = advantages,
                        old_logps = old_logps,
                        ref_logps = ref_logps,
                        n_chunks = self.args.unsloth_num_chunks,
                        temperature = self.args.temperature,
                        logit_softcapping = logit_softcapping,
                        logit_scale_multiply = logit_scale_multiply,
                        logit_scale_divide = logit_scale_divide,
                        attention_mask = attention_mask,
                        token_type_ids = token_type_ids,
                        mm_token_type_ids = mm_token_type_ids,
                    )
                )
        if "train" in self._metrics:
            mode = "eval" if self.control.should_evaluate else "train"
            self._metrics[mode]["completion_length"].append(completion_length.item())
            self._metrics[mode]["kl"].append(mean_kl.item())
        else:
            self._metrics["completion_length"].append(completion_length.item())
            self._metrics["kl"].append(mean_kl.item())

        if (
            self.use_vllm
            and delta is not None
            and getattr(self, "vllm_importance_sampling_correction", False)
        ):
            mean_delta = (
                torch.mean(delta)
                if delta.numel() > 0
                else torch.tensor(0.0, device = self.model.device)
            )
            max_delta = (
                torch.max(delta)
                if delta.numel() > 0
                else torch.tensor(0.0, device = self.model.device)
            )
            self._metrics[mode]["sampling/sampling_logp_difference/mean"].append(
                self.accelerator.gather(mean_delta).mean().item()
            )
            self._metrics[mode]["sampling/sampling_logp_difference/max"].append(
                self.accelerator.gather(max_delta).max().item()
            )

            min_importance_sampling_ratio = (
                torch.min(flat_is_ratio)
                if flat_is_ratio.numel() > 0
                else torch.tensor(0.0, device = self.model.device)
            )
            mean_importance_sampling_ratio = (
                torch.mean(flat_is_ratio)
                if flat_is_ratio.numel() > 0
                else torch.tensor(0.0, device = self.model.device)
            )
            max_importance_sampling_ratio = (
                torch.max(flat_is_ratio)
                if flat_is_ratio.numel() > 0
                else torch.tensor(0.0, device = self.model.device)
            )
            self._metrics[mode]["sampling/importance_sampling_ratio/min"].append(
                self.accelerator.gather(min_importance_sampling_ratio)
                .nan_to_num(nan = float("inf"))
                .min()
                .item()
            )
            self._metrics[mode]["sampling/importance_sampling_ratio/mean"].append(
                self.accelerator.gather(mean_importance_sampling_ratio).nanmean().item()
            )
            self._metrics[mode]["sampling/importance_sampling_ratio/max"].append(
                self.accelerator.gather(max_importance_sampling_ratio)
                .nan_to_num(nan = float("-inf"))
                .max()
                .item()
            )

        completion_token_count = completion_mask.sum().clamp(min = 1.0)

        def masked_batch_mean(x):
            if x.shape[1] == 1:  # when importance_sampling_level == "sequence"
                return x.mean()
            else:
                return (x * completion_mask).sum() / completion_token_count

        if advantages.dim() == 1:
            advantages = advantages.unsqueeze(1)

        if self.loss_type in ["grpo", "bnpo", "dr_grpo", "dapo"]:
            # Compute the clipped probability ratios
            is_low_clipped = (coef_1 < 1 - self.epsilon_low) & (advantages < 0)
            is_high_clipped = (coef_1 > 1 + self.epsilon_high) & (advantages > 0)
            is_region_clipped = is_low_clipped | is_high_clipped

            low_clip = masked_batch_mean(is_low_clipped.float())
            high_clip = masked_batch_mean(is_high_clipped.float())
            clip_ratio = masked_batch_mean(is_region_clipped.float())

            gathered_low_clip = self.accelerator.gather(low_clip)
            self._metrics[mode]["clip_ratio/low_mean"].append(
                gathered_low_clip.nanmean().item()
            )
            self._metrics[mode]["clip_ratio/low_min"].append(
                nanmin(gathered_low_clip).item()
            )
            gathered_high_clip = self.accelerator.gather(high_clip)
            self._metrics[mode]["clip_ratio/high_mean"].append(
                gathered_high_clip.nanmean().item()
            )
            self._metrics[mode]["clip_ratio/high_max"].append(
                nanmax(gathered_high_clip).item()
            )
            gathered_clip_ratio = self.accelerator.gather(clip_ratio)
            self._metrics[mode]["clip_ratio/region_mean"].append(
                gathered_clip_ratio.nanmean().item()
            )
        elif self.loss_type == "cispo":
            is_cispo_clipped = (coef_1 > self.epsilon_high) & (advantages > 0)
            cispo_clip_ratio = masked_batch_mean(is_cispo_clipped.float())
            gathered_cispo_clip_ratio = self.accelerator.gather(cispo_clip_ratio)
            self._metrics[mode]["cispo_clip_ratio"].append(
                gathered_cispo_clip_ratio.nanmean().item()
            )

        return loss