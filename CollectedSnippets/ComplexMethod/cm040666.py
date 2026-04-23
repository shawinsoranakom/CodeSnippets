def _flatten_metrics_in_order(self, logs):
        """Turns `logs` dict into a list as per key order of `metrics_names`."""
        metric_names = []
        for metric in self.metrics:
            if isinstance(metric, CompileMetrics):
                metric_names += [
                    sub_metric.name for sub_metric in metric.metrics
                ]
            else:
                metric_names.append(metric.name)
        results = []
        for name in metric_names:
            if name in logs:
                results.append(logs[name])
        for key in sorted(logs.keys()):
            if key not in metric_names:
                results.append(logs[key])
        if len(results) == 1:
            return results[0]
        return results