def _determine_best_metric(self, metrics: dict[str, float], trial: "optuna.Trial | dict[str, Any] | None") -> bool:
        """
        Determine if the model should be saved based on the evaluation metrics.

        Returns:
            bool: True if a new best metric was found, else False
        """
        is_new_best_metric = False

        if self.args.metric_for_best_model is not None:
            metric_to_check = self.args.metric_for_best_model

            if not metric_to_check.startswith("eval_"):
                metric_to_check = f"eval_{metric_to_check}"

            try:
                metric_value = metrics[metric_to_check]
            except KeyError as exc:
                raise KeyError(
                    f"The `metric_for_best_model` training argument is set to '{metric_to_check}', which is not found in the evaluation metrics. "
                    f"The available evaluation metrics are: {list(metrics.keys())}. Consider changing the `metric_for_best_model` via the TrainingArguments."
                ) from exc

            operator = np.greater if self.args.greater_is_better else np.less

            if self.state.best_metric is None:
                self.state.best_metric = float("-inf") if self.args.greater_is_better else float("inf")

            if operator(metric_value, self.state.best_metric):
                self.state.best_metric = metric_value

                if self.args.save_strategy in [SaveStrategy.STEPS, SaveStrategy.EPOCH, SaveStrategy.BEST]:
                    self.state.best_global_step = self.state.global_step

                is_new_best_metric = True

        return is_new_best_metric