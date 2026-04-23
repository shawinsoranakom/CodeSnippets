def _validate_args(self):
        """Validate argument combinations and value constraints."""
        if self.torch_empty_cache_steps is not None:
            if not (isinstance(self.torch_empty_cache_steps, int) and self.torch_empty_cache_steps > 0):
                raise ValueError(
                    f"`torch_empty_cache_steps` must be an integer bigger than 0, got {self.torch_empty_cache_steps}."
                )

        # logging_steps must be non-zero when logging_strategy="steps"
        if self.logging_strategy == IntervalStrategy.STEPS and self.logging_steps == 0:
            raise ValueError(f"logging strategy {self.logging_strategy} requires non-zero --logging_steps")

        if self.logging_strategy == IntervalStrategy.STEPS and self.logging_steps > 1:
            if self.logging_steps != int(self.logging_steps):
                raise ValueError(f"--logging_steps must be an integer if bigger than 1: {self.logging_steps}")
            self.logging_steps = int(self.logging_steps)
        if self.eval_strategy == IntervalStrategy.STEPS and self.eval_steps > 1:
            if self.eval_steps != int(self.eval_steps):
                raise ValueError(f"--eval_steps must be an integer if bigger than 1: {self.eval_steps}")
            self.eval_steps = int(self.eval_steps)
        if self.save_strategy == SaveStrategy.STEPS and self.save_steps > 1:
            if self.save_steps != int(self.save_steps):
                raise ValueError(f"--save_steps must be an integer if bigger than 1: {self.save_steps}")
            self.save_steps = int(self.save_steps)

        # load_best_model_at_end requires compatible save and eval strategies
        if self.load_best_model_at_end and self.save_strategy != SaveStrategy.BEST:
            if self.eval_strategy != self.save_strategy:
                raise ValueError(
                    '--load_best_model_at_end requires the save and eval strategy to match, except when --save_strategy="best", but found\n- Evaluation '
                    f"strategy: {self.eval_strategy}\n- Save strategy: {self.save_strategy}"
                )
            if self.eval_strategy == IntervalStrategy.STEPS and self.save_steps % self.eval_steps != 0:
                if self.eval_steps < 1 or self.save_steps < 1:
                    if not (self.eval_steps < 1 and self.save_steps < 1):
                        raise ValueError(
                            "--load_best_model_at_end requires the saving steps to be a multiple of the evaluation "
                            "steps, which cannot get guaranteed when mixing ratio and absolute steps for save_steps "
                            f"{self.save_steps} and eval_steps {self.eval_steps}."
                        )
                    # Use integer arithmetic to avoid floating point precision issues
                    LARGE_MULTIPLIER = 1_000_000
                    if (self.save_steps * LARGE_MULTIPLIER) % (self.eval_steps * LARGE_MULTIPLIER) != 0:
                        raise ValueError(
                            "--load_best_model_at_end requires the saving steps to be a multiple of the evaluation "
                            f"steps, but found {self.save_steps}, which is not a multiple of {self.eval_steps}."
                        )
                else:
                    raise ValueError(
                        "--load_best_model_at_end requires the saving steps to be a round multiple of the evaluation "
                        f"steps, but found {self.save_steps}, which is not a round multiple of {self.eval_steps}."
                    )

        if is_torch_available():
            if self.bf16 or self.bf16_full_eval:
                if not self.use_cpu and not is_torch_bf16_gpu_available() and not is_torch_xla_available():
                    error_message = "Your setup doesn't support bf16/gpu. You need to assign use_cpu if you want to train the model on CPU."
                    if is_torch_cuda_available():
                        error_message += " You need Ampere+ GPU with cuda>=11.0."
                    raise ValueError(error_message)

        if self.fp16 and self.bf16:
            raise ValueError("At most one of fp16 and bf16 can be True, but not both")

        if self.fp16_full_eval and self.bf16_full_eval:
            raise ValueError("At most one of fp16 and bf16 can be True for full eval, but not both")

        if self.lr_scheduler_type == SchedulerType.REDUCE_ON_PLATEAU:
            if self.eval_strategy == IntervalStrategy.NO:
                raise ValueError("lr_scheduler_type reduce_lr_on_plateau requires an eval strategy")
            if not is_torch_available():
                raise ValueError("lr_scheduler_type reduce_lr_on_plateau requires torch>=0.2.0")

        if self.lr_scheduler_type == SchedulerType.GREEDY:
            if self.eval_strategy == IntervalStrategy.NO:
                raise ValueError("lr_scheduler_type greedy requires an eval strategy")

        if self.warmup_steps < 0:
            raise ValueError("warmup_steps must be an integer or a float")

        if self.dataloader_num_workers == 0 and self.dataloader_prefetch_factor is not None:
            raise ValueError(
                "--dataloader_prefetch_factor can only be set when data is loaded in a different process, i.e."
                " when --dataloader_num_workers > 0."
            )