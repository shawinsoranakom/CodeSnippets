def test_multiple_decorators_on_different_services(self, clean_manager):
        """Test registering multiple different services."""
        clean_manager.register_service_class(ServiceType.STORAGE_SERVICE, LocalStorageService, override=True)
        clean_manager.register_service_class(ServiceType.TELEMETRY_SERVICE, TelemetryService, override=True)
        clean_manager.register_service_class(ServiceType.TRACING_SERVICE, TracingService, override=True)

        # All should be registered (plus MockSessionService from fixture)
        assert len(clean_manager.service_classes) == 4
        assert ServiceType.STORAGE_SERVICE in clean_manager.service_classes
        assert ServiceType.TELEMETRY_SERVICE in clean_manager.service_classes
        assert ServiceType.TRACING_SERVICE in clean_manager.service_classes

        # All should be creatable
        storage = clean_manager.get(ServiceType.STORAGE_SERVICE)
        telemetry = clean_manager.get(ServiceType.TELEMETRY_SERVICE)
        tracing = clean_manager.get(ServiceType.TRACING_SERVICE)

        assert isinstance(storage, LocalStorageService)
        assert isinstance(telemetry, TelemetryService)
        assert isinstance(tracing, TracingService)