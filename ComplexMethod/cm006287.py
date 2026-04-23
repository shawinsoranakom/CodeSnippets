def end(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        error: Exception | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Build hierarchy and send using SDK."""
        # Early guard return before entering try/finally
        if not self._ready or not self.trace_obj:
            return

        try:
            # Build hierarchy and add to trace
            # This will integrate handler's traces and then clear them
            self._build_and_add_hierarchy(
                flow_inputs=inputs,
                flow_outputs=outputs,
                error=error,
                flow_metadata=metadata,
            )

            # Use SDK's post_process_trace
            try:
                trace_data, input_variable_names = self._openlayer_tracer.post_process_trace(self.trace_obj)
            except Exception:  # noqa: BLE001
                return  # finally block will still execute

            # Validate trace_data
            if not trace_data or not isinstance(trace_data, dict):
                return  # finally block will still execute

            # Aggregate token/model data from nested ChatCompletionSteps.
            # post_process_trace only reads tokens from the root step (UserCallStep),
            # which has no token data. We walk nested steps to surface this info.
            self._aggregate_llm_data(trace_data)

            # Build config using SDK's ConfigLlmData
            config = dict(
                self._openlayer_tracer.ConfigLlmData(
                    output_column_name="output",
                    input_variable_names=input_variable_names,
                    latency_column_name="latency",
                    cost_column_name="cost",
                    timestamp_column_name="inferenceTimestamp",
                    inference_id_column_name="inferenceId",
                    num_of_token_column_name="tokens",  # noqa: S106
                )
            )

            # Add reserved column configurations
            if "user_id" in trace_data:
                config["user_id_column_name"] = "user_id"
            if "session_id" in trace_data:
                config["session_id_column_name"] = "session_id"
            if "context" in trace_data:
                config["context_column_name"] = "context"

            # Send using our own client (we disabled auto-publish, so we always upload here)
            if self._client:
                self._client.inference_pipelines.data.stream(
                    inference_pipeline_id=self._inference_pipeline_id,
                    rows=[trace_data],
                    config=config,
                )

        except Exception as e:  # noqa: BLE001
            # Log unexpected exceptions for troubleshooting
            logger.debug("Openlayer tracer end() failed: {}", e)
        finally:
            # Always clean up SDK context regardless of early returns or exceptions
            self._cleanup_sdk_context()