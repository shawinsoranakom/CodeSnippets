def fit(self) -> None:
        """Train the model."""
        self.model.train()
        self.callback_handler.on_train_begin(self.args, self.state)
        for epoch in range(self._resume_epoch, self.args.num_train_epochs):
            self.state.epoch = epoch
            self.train_batch_generator.set_epoch(epoch)
            self.callback_handler.on_epoch_begin(self.args, self.state)

            for micro_batches in self.train_batch_generator:
                self.global_step += 1

                self.state.global_step = self.global_step
                self.callback_handler.on_step_begin(self.args, self.state)

                step_loss = 0
                step_valid_tokens = compute_valid_tokens(micro_batches)
                step_valid_tokens = DistributedInterface().all_reduce(step_valid_tokens, op=ReduceOp.SUM)
                num_micro = len(micro_batches)
                for i, micro_batch in enumerate(micro_batches):
                    if self.args.dist_config and self.args.dist_config.get("cp_size", 1) > 1:
                        from ..plugins.model_plugins.parallelization.sequence_parallel import (
                            SequenceParallelLossPlugin,
                        )

                        loss = SequenceParallelLossPlugin("sequence_parallel_loss")(self.model, micro_batch)
                    else:
                        loss = self.compute_loss(micro_batch)
                    mini_step_valid_tokens = compute_valid_tokens([micro_batch])
                    # fsdp uses mean reduction so we need to scale the loss by dp_size
                    loss = loss * mini_step_valid_tokens * self.dp_size / (step_valid_tokens + 1e-6)

                    if self._deepspeed_engine is not None:
                        # deepspeed: set sync_gradients so engine.step() only fires on last micro-batch
                        self._deepspeed_engine.accelerator.sync_gradients = i == num_micro - 1
                        self._deepspeed_engine.backward(loss)
                    else:
                        loss.backward()
                    step_loss += loss.item()

                if self._deepspeed_engine is not None:
                    # deepspeed: engine.step() already ran inside backward at the sync boundary
                    grad_norm = self._deepspeed_engine.get_grad_norm()
                else:
                    if self.args.dist_config and self.args.dist_config.get("cp_size", 1) > 1:
                        from torch.nn.utils.clip_grad import _clip_grads_with_norm_, _get_total_norm

                        parameters = self.model.parameters()
                        if isinstance(parameters, torch.Tensor):
                            parameters = [parameters]
                        else:
                            parameters = list(parameters)
                        grads = [p.grad for p in parameters if p.grad is not None]
                        grad_norm = _get_total_norm(grads)
                        grad_norm = grad_norm.to(self.device)
                        _clip_grads_with_norm_(parameters, self.args.max_grad_norm, grad_norm)
                        if isinstance(grad_norm, torch.distributed._tensor.DTensor):
                            grad_norm = grad_norm.full_tensor().item()
                    else:
                        grad_norm = torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), self.args.max_grad_norm
                        ).item()

                    # isfinite(): argument 'input' (position 1) must be Tensor, not float
                    if not torch.isfinite(torch.tensor(grad_norm)):  # type: ignore # pyright: ignore [reportUnknownReturnType]
                        logger.warning_rank0(f"Gradient norm is not finite: {grad_norm}")
                    else:
                        self.optimizer.step()

                    self.lr_scheduler.step()
                    self.optimizer.zero_grad()

                step_loss, grad_norm = DistributedInterface().all_reduce([step_loss, grad_norm])
                DistributedInterface().sync()

                # Update state with step metrics
                current_lr = (
                    self.lr_scheduler.get_last_lr()[0]
                    if hasattr(self.lr_scheduler, "get_last_lr")
                    else self.args.learning_rate
                )
                self.state.loss = step_loss
                self.state.grad_norm = grad_norm
                self.state.learning_rate = current_lr

                self.callback_handler.on_step_end(self.args, self.state)

                # Logging: trainer decides when to log
                if self.global_step % self.args.logging_steps == 0:
                    logs = {
                        "epoch": epoch,
                        "step": self.global_step,
                        "loss": step_loss,
                        "grad_norm": grad_norm,
                        "learning_rate": current_lr,
                    }
                    self.callback_handler.on_log(self.args, self.state, logs)

                if self.args.save_steps and self.global_step % self.args.save_steps == 0:
                    self._checkpoint.save(epoch)

                # Check if max_steps is reached
                if self.global_step >= self.num_training_steps:
                    logger.info_rank0(f"Reached max_steps ({self.num_training_steps}), stopping training.")
                    self.callback_handler.on_epoch_end(self.args, self.state)
                    self.callback_handler.on_train_end(self.args, self.state)
                    return

            self.callback_handler.on_epoch_end(self.args, self.state)

        self.callback_handler.on_train_end(self.args, self.state)