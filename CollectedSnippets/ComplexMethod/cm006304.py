def setup_arize_phoenix(self) -> bool:
        """Configures Arize/Phoenix specific environment variables and registers the tracer provider."""
        arize_phoenix_batch = os.getenv("ARIZE_PHOENIX_BATCH", "False").lower() in {
            "true",
            "t",
            "yes",
            "y",
            "1",
        }

        # Arize Config
        arize_api_key = os.getenv("ARIZE_API_KEY", None)
        arize_space_id = os.getenv("ARIZE_SPACE_ID", None)
        arize_collector_endpoint = os.getenv("ARIZE_COLLECTOR_ENDPOINT", "https://otlp.arize.com")
        enable_arize_tracing = bool(arize_api_key and arize_space_id)
        arize_endpoint = f"{arize_collector_endpoint}/v1"
        arize_headers = {
            "api_key": arize_api_key,
            "space_id": arize_space_id,
            "authorization": f"Bearer {arize_api_key}",
        }

        # Phoenix Config
        phoenix_api_key = os.getenv("PHOENIX_API_KEY", None)
        phoenix_collector_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com")
        phoenix_auth_disabled = "localhost" in phoenix_collector_endpoint or "127.0.0.1" in phoenix_collector_endpoint
        enable_phoenix_tracing = bool(phoenix_api_key) or phoenix_auth_disabled
        phoenix_endpoint = f"{phoenix_collector_endpoint}/v1/traces"
        phoenix_headers = (
            {
                "api_key": phoenix_api_key,
                "authorization": f"Bearer {phoenix_api_key}",
            }
            if phoenix_api_key
            else {}
        )

        if not (enable_arize_tracing or enable_phoenix_tracing):
            return False

        try:
            from phoenix.otel import (
                PROJECT_NAME,
                BatchSpanProcessor,
                GRPCSpanExporter,
                HTTPSpanExporter,
                Resource,
                SimpleSpanProcessor,
                TracerProvider,
            )

            name_without_space = self.flow_name.replace(" ", "-")
            project_name = self.project_name if name_without_space == "None" else name_without_space
            attributes = {PROJECT_NAME: project_name, "model_id": project_name}
            resource = Resource.create(attributes=attributes)
            tracer_provider = TracerProvider(resource=resource, verbose=False)
            span_processor = BatchSpanProcessor if arize_phoenix_batch else SimpleSpanProcessor

            if enable_arize_tracing:
                tracer_provider.add_span_processor(
                    span_processor=span_processor(
                        span_exporter=GRPCSpanExporter(endpoint=arize_endpoint, headers=arize_headers),
                    )
                )

            if enable_phoenix_tracing:
                tracer_provider.add_span_processor(
                    span_processor=span_processor(
                        span_exporter=HTTPSpanExporter(
                            endpoint=phoenix_endpoint,
                            headers=phoenix_headers,
                        ),
                    )
                )

            tracer_provider.add_span_processor(CollectingSpanProcessor())
            self.tracer_provider = tracer_provider
        except ImportError:
            logger.exception(
                "[Arize/Phoenix] Could not import Arize Phoenix OTEL packages."
                "Please install it with `pip install arize-phoenix-otel`."
            )
            return False

        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor

            LangChainInstrumentor().instrument(tracer_provider=self.tracer_provider, skip_dep_check=True)
        except ImportError:
            logger.exception(
                "[Arize/Phoenix] Could not import LangChainInstrumentor."
                "Please install it with `pip install openinference-instrumentation-langchain`."
            )
            return False

        return True