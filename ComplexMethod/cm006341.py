def __init__(self, *, prometheus_enabled: bool = True):
        # Only initialize once
        self.prometheus_enabled = prometheus_enabled
        if OpenTelemetry._initialized:
            return

        if not self._metrics_registry:
            self._register_metric()

        if self._meter_provider is None:
            # Get existing meter provider if any
            existing_provider = metrics.get_meter_provider()

            # Check if FastAPI instrumentation is already set up
            if hasattr(existing_provider, "get_meter") and existing_provider.get_meter("http.server"):
                self._meter_provider = existing_provider
            else:
                resource = Resource.create({"service.name": "langflow"})
                metric_readers = []
                if self.prometheus_enabled:
                    metric_readers.append(PrometheusMetricReader())

                self._meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
                metrics.set_meter_provider(self._meter_provider)

        self.meter = self._meter_provider.get_meter(langflow_meter_name)

        for name, metric in self._metrics_registry.items():
            if name != metric.name:
                msg = f"Key '{name}' does not match metric name '{metric.name}'"
                raise ValueError(msg)
            if name not in self._metrics:
                self._metrics[metric.name] = self._create_metric(metric)

        OpenTelemetry._initialized = True