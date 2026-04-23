def test_langsmith_inheritable_metadata_copies_handlers_without_mutating_original(
        self,
    ) -> None:
        """Configured manager copies tracers and leaves the original unchanged."""
        tracer = _create_tracer_with_mocked_client()
        cm = CallbackManager.configure(
            inheritable_callbacks=[tracer],
            langsmith_inheritable_metadata={"env": "prod"},
        )
        handler_tracer = next(h for h in cm.handlers if isinstance(h, LangChainTracer))
        inheritable_tracer = next(
            h for h in cm.inheritable_handlers if isinstance(h, LangChainTracer)
        )
        assert handler_tracer is not tracer
        assert inheritable_tracer is not tracer
        assert tracer.tracing_metadata is None