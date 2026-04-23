def _report_to_hp_search(
        self, trial: "optuna.Trial | dict[str, Any] | None", step: int, metrics: dict[str, float]
    ) -> None:
        """Report intermediate metrics to the active hyperparameter search backend."""
        if self.hp_search_backend is None or trial is None:
            return
        metrics = metrics.copy()
        self.objective = self.compute_objective(metrics)
        if self.hp_search_backend == HPSearchBackend.OPTUNA:
            import optuna

            if hasattr(trial, "study") and not trial.study._is_multi_objective():
                trial.report(self.objective, step)
                if trial.should_prune():
                    self.callback_handler.on_train_end(self.args, self.state, self.control)
                    raise optuna.TrialPruned()
        elif self.hp_search_backend == HPSearchBackend.RAY:
            import ray.tune

            with tempfile.TemporaryDirectory() as temp_checkpoint_dir:
                checkpoint = None
                if self.control.should_save:
                    self._tune_save_checkpoint(checkpoint_dir=temp_checkpoint_dir)
                    checkpoint = ray.tune.Checkpoint.from_directory(temp_checkpoint_dir)
                metrics["objective"] = self.objective
                ray.tune.report(metrics, checkpoint=checkpoint)