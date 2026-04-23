def test_init_with_metrics_data(self):
        """Test initialization with metrics data."""
        metrics_data = {
            'cpu_usage': 75.5,
            'memory_usage': 1024,
            'active_sessions': 5,
        }

        metrics = TelemetryMetrics(metrics_data=metrics_data)

        assert metrics.metrics_data == metrics_data
        assert metrics.upload_attempts == 0
        assert metrics.uploaded_at is None
        assert metrics.last_upload_error is None
        assert metrics.collected_at is not None
        assert metrics.created_at is not None
        assert metrics.updated_at is not None