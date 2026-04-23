def test_langsmith_inheritable_metadata_configure_isolated_per_manager(
        self,
    ) -> None:
        """Separate configure calls keep tracer-only defaults isolated."""
        tracer = _create_tracer_with_mocked_client()
        alpha_manager = CallbackManager.configure(
            inheritable_callbacks=[tracer],
            langsmith_inheritable_metadata={"tenant": "alpha"},
        )
        beta_manager = CallbackManager.configure(
            inheritable_callbacks=[tracer],
            langsmith_inheritable_metadata={"tenant": "beta"},
        )

        alpha_tracer = next(
            handler
            for handler in alpha_manager.handlers
            if isinstance(handler, LangChainTracer)
        )
        beta_tracer = next(
            handler
            for handler in beta_manager.handlers
            if isinstance(handler, LangChainTracer)
        )

        assert tracer.tracing_metadata is None
        assert alpha_tracer is not tracer
        assert beta_tracer is not tracer
        assert alpha_tracer is not beta_tracer
        assert alpha_tracer.tracing_metadata == {"tenant": "alpha"}
        assert beta_tracer.tracing_metadata == {"tenant": "beta"}
        assert alpha_tracer.run_map is tracer.run_map
        assert beta_tracer.run_map is tracer.run_map
        assert alpha_tracer.order_map is tracer.order_map
        assert beta_tracer.order_map is tracer.order_map