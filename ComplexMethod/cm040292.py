def _set_monitor_op(self):
        if self.mode == "min":
            self.monitor_op = ops.less
        elif self.mode == "max":
            self.monitor_op = ops.greater
        else:
            metric_name = self.monitor.removeprefix("val_")
            if metric_name == "loss":
                self.monitor_op = ops.less
            if hasattr(self.model, "metrics"):
                all_metrics = []
                for m in self.model.metrics:
                    if isinstance(
                        m,
                        (
                            compile_utils.CompileMetrics,
                            compile_utils.MetricsList,
                        ),
                    ):
                        all_metrics.extend(m.metrics)
                for m in all_metrics:
                    if m.name == metric_name:
                        if hasattr(m, "_direction"):
                            if m._direction == "up":
                                self.monitor_op = ops.greater
                            else:
                                self.monitor_op = ops.less
            if self.monitor_op is None:
                raise ValueError(
                    f"{self.__class__.__name__} callback received "
                    f"monitor={self.monitor}, but Keras isn't able to "
                    "automatically determine whether that metric should be "
                    "maximized or minimized. Pass `mode='max'` in order to "
                    "monitor based on the highest metric value, or pass "
                    "`mode='min'` in order to use the lowest value."
                )
        if self.monitor_op == ops.less:
            self.min_delta *= -1