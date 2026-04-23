def on_step_end(self, args, state, control, **kwargs):
        if not self._initialized or not state.is_world_process_zero:
            return

        if not state.max_steps or state.max_steps <= 0:
            return

        import time

        progress = int((state.global_step / state.max_steps) * 100)
        # Cap at 99% until on_train_end reports 100% to indicate completion
        progress = min(progress, 99)

        eta_seconds = None
        if self._start_time and state.global_step > 0:
            elapsed = time.time() - self._start_time
            avg_time_per_step = elapsed / state.global_step
            remaining_steps = state.max_steps - state.global_step
            eta_seconds = int(avg_time_per_step * remaining_steps)

        metrics = {
            **self._metrics,
            "current_step": state.global_step,
            "total_steps": state.max_steps,
        }
        if state.epoch is not None:
            metrics["current_epoch"] = round(state.epoch, 2)

        self._update_status(
            progress_percent=progress,
            estimated_time_remaining=eta_seconds,
            metrics=metrics,
        )