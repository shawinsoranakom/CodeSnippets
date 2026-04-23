def on_log(self, args, state, control, logs = None, **kwargs):
                if not logs:
                    return
                loss_value = logs.get("loss", logs.get("train_loss", None))
                current_step = state.global_step
                grad_norm = logs.get("grad_norm", None)

                elapsed_seconds = None
                if trainer_ref.training_start_time is not None:
                    elapsed_seconds = time.time() - trainer_ref.training_start_time

                eta_seconds = None
                if elapsed_seconds is not None and current_step > 0:
                    total_steps = trainer_ref.training_progress.total_steps
                    if total_steps > 0:
                        steps_remaining = total_steps - current_step
                        if steps_remaining > 0:
                            eta_seconds = (
                                elapsed_seconds / current_step
                            ) * steps_remaining

                num_tokens = getattr(state, "num_input_tokens_seen", None)

                trainer_ref._update_progress(
                    step = current_step,
                    epoch = round(state.epoch, 2) if state.epoch else 0,
                    loss = loss_value,
                    learning_rate = logs.get("learning_rate", None),
                    elapsed_seconds = elapsed_seconds,
                    eta_seconds = eta_seconds,
                    grad_norm = grad_norm,
                    num_tokens = num_tokens,
                    eval_loss = logs.get("eval_loss", None),
                    status_message = "",
                )