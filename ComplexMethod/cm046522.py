def build_progress(
            step: int,
            loss: Optional[float],
            learning_rate: Optional[float],
            total_steps: int,
            epoch: Optional[float] = None,
            progress: Optional[Any] = None,
            grad_norm_override: Optional[float] = None,
            eval_loss_override: Optional[float] = None,
        ) -> TrainingProgress:
            total = max(total_steps, 0)
            if step < 0 or total == 0:
                progress_percent = 0.0
            else:
                progress_percent = (
                    float(step) / float(total) * 100.0 if total > 0 else 0.0
                )

            # Get actual values from progress object if available
            elapsed_seconds = (
                getattr(progress, "elapsed_seconds", None) if progress else None
            )
            eta_seconds = getattr(progress, "eta_seconds", None) if progress else None
            grad_norm = grad_norm_override
            if grad_norm is None and progress:
                grad_norm = getattr(progress, "grad_norm", None)
            num_tokens = getattr(progress, "num_tokens", None) if progress else None
            eval_loss = eval_loss_override
            if eval_loss is None and progress:
                eval_loss = getattr(progress, "eval_loss", None)

            return TrainingProgress(
                job_id = job_id,
                step = step,
                total_steps = total,
                loss = loss,
                learning_rate = learning_rate,
                progress_percent = progress_percent,
                epoch = epoch,
                elapsed_seconds = elapsed_seconds,
                eta_seconds = eta_seconds,
                grad_norm = grad_norm,
                num_tokens = num_tokens,
                eval_loss = eval_loss,
            )