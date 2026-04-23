def _get_config(trace_name: str | None = None) -> dict:
        """Get Openlayer configuration from environment variables.

        Configuration is resolved in the following order (highest priority first):
        1. Flow-specific env var: OPENLAYER_PIPELINE_<FLOW_NAME>
        2. JSON mapping: OPENLAYER_LANGFLOW_MAPPING
        3. Default env var: OPENLAYER_INFERENCE_PIPELINE_ID

        Args:
            trace_name: The trace name which may contain the flow name

        Returns:
            Configuration dict with 'api_key' and 'inference_pipeline_id', or empty dict
        """
        api_key = os.getenv("OPENLAYER_API_KEY", None)
        if not api_key:
            return {}

        inference_pipeline_id = None

        # Extract flow name from trace_name (format: "flow_name - flow_id")
        flow_name = None
        if trace_name:
            flow_name, _ = OpenlayerTracer._parse_trace_name(trace_name)

        # 1. Try flow-specific environment variable (highest priority)
        if flow_name:
            sanitized_flow_name = OpenlayerTracer._sanitize_flow_name(flow_name)
            flow_specific_var = f"OPENLAYER_PIPELINE_{sanitized_flow_name}"
            inference_pipeline_id = os.getenv(flow_specific_var)

        # 2. Try JSON mapping (medium priority)
        if not inference_pipeline_id:
            mapping_json = os.getenv("OPENLAYER_LANGFLOW_MAPPING")
            if mapping_json and flow_name:
                try:
                    mapping = json.loads(mapping_json)
                    if isinstance(mapping, dict) and flow_name in mapping:
                        inference_pipeline_id = mapping[flow_name]
                except json.JSONDecodeError:
                    pass

        # 3. Fall back to default environment variable (lowest priority)
        if not inference_pipeline_id:
            inference_pipeline_id = os.getenv("OPENLAYER_INFERENCE_PIPELINE_ID")

        if api_key and inference_pipeline_id:
            return {
                "api_key": api_key,
                "inference_pipeline_id": inference_pipeline_id,
            }

        return {}