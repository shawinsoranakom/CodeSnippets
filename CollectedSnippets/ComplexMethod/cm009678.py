def test_copy_with_metadata_defaults_copies_configuration(self) -> None:
        """Copied tracer keeps stable configuration but not identity."""
        tracer = self._make_tracer(metadata={"env": "staging"})
        tracer.project_name = "project"
        tracer.tags = ["tag"]

        copied = tracer.copy_with_metadata_defaults(metadata={"service": "api"})

        assert copied is not tracer
        assert copied.client is tracer.client
        assert copied.project_name == "project"
        assert copied.tags == ["tag"]
        assert copied.tags is tracer.tags
        assert copied.tracing_metadata == {"env": "staging", "service": "api"}
        assert copied.run_map is tracer.run_map
        assert copied.order_map is tracer.order_map
        assert copied.run_has_token_event_map == {}