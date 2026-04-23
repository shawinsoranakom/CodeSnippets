def setup_openlayer(self, config) -> bool:
        """Initialize Openlayer SDK utilities."""
        # Validate configuration
        if not config:
            logger.debug("Openlayer tracer not initialized: empty configuration")
            return False

        required_keys = ["api_key", "inference_pipeline_id"]
        for key in required_keys:
            if key not in config or not config[key]:
                logger.debug("Openlayer tracer not initialized: missing required key '{}'", key)
                return False

        try:
            from openlayer import Openlayer
            from openlayer.lib.tracing import configure
            from openlayer.lib.tracing import enums as openlayer_enums
            from openlayer.lib.tracing import steps as openlayer_steps
            from openlayer.lib.tracing import tracer as openlayer_tracer
            from openlayer.lib.tracing import traces as openlayer_traces
            from openlayer.lib.tracing.context import UserSessionContext

            self._openlayer_tracer = openlayer_tracer
            self._openlayer_steps = openlayer_steps
            self._openlayer_traces = openlayer_traces
            self._openlayer_enums = openlayer_enums
            self._user_session_context = UserSessionContext
            self._inference_pipeline_id = config["inference_pipeline_id"]

            # Create our own client for manual uploads (bypasses _publish check)
            self._client = Openlayer(api_key=config["api_key"])

            if self.user_id:
                self._user_session_context.set_user_id(self.user_id)
            if self.session_id:
                self._user_session_context.set_session_id(self.session_id)

            # Disable auto-publishing to prevent duplicate uploads.
            # We manually upload in end() method using self._client.
            # Setting the module-level _publish directly is required because
            # the env var OPENLAYER_DISABLE_PUBLISH is only read at import time.
            openlayer_tracer._publish = False
            configure(inference_pipeline_id=config["inference_pipeline_id"])

            # Build step type map once for reuse in add_trace
            self._step_type_map = {
                "llm": self._openlayer_enums.StepType.CHAT_COMPLETION,
                "chain": self._openlayer_enums.StepType.USER_CALL,
                "tool": self._openlayer_enums.StepType.TOOL,
                "agent": self._openlayer_enums.StepType.AGENT,
                "retriever": self._openlayer_enums.StepType.RETRIEVER,
                "prompt": self._openlayer_enums.StepType.USER_CALL,
            }
        except ImportError as e:
            logger.debug("Openlayer tracer not initialized: import error - {}", e)
            return False
        except Exception as e:  # noqa: BLE001
            logger.debug("Openlayer tracer not initialized: unexpected error - {}", e)
            return False
        else:
            return True