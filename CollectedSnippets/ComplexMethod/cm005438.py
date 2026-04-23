def on_log(self, args, state, control, logs, model=None, **kwargs):
        if not self._initialized:
            self.setup(args, state, model)
        if state.is_world_process_zero:
            metrics = {}
            for k, v in logs.items():
                if isinstance(v, (int, float)):
                    metrics[k] = v
                elif isinstance(v, torch.Tensor) and v.numel() == 1:
                    metrics[k] = v.item()
                else:
                    logger.warning(
                        f'Trainer is attempting to log a value of "{v}" of type {type(v)} for key "{k}" as a metric. '
                        "MLflow's log_metric() only accepts float and int types so we dropped this attribute."
                    )

            # sanitize metric names to replace unsupported characters like parentheses
            sanitized_metrics = {re.sub(r"[^0-9A-Za-z_\-\.\ :/]", "_", k): v for k, v in metrics.items()}

            if self._async_log:
                self._ml_flow.log_metrics(metrics=sanitized_metrics, step=state.global_step, synchronous=False)
            else:
                self._ml_flow.log_metrics(metrics=sanitized_metrics, step=state.global_step)