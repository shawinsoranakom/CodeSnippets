def grammar_init(self, request: "Request") -> None:
        if request.structured_output_request is None:
            return

        if TYPE_CHECKING:
            assert (
                request.sampling_params is not None
                and request.sampling_params.structured_outputs is not None
            )

        # Initialize the backend the first time it is needed.
        #
        # NOTE: We only support a single backend. We do NOT support different
        # backends on a per-request basis in V1 (for now, anyway...).
        # _backend is set in Processor._validate_structured_output
        if self.backend is None:
            assert request.sampling_params is not None
            backend = request.sampling_params.structured_outputs._backend
            vocab_size = self.vllm_config.model_config.get_vocab_size()
            if backend == "xgrammar":
                self.backend = XgrammarBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            elif backend == "guidance":
                self.backend = GuidanceBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            elif backend == "outlines":
                from vllm.v1.structured_output.backend_outlines import OutlinesBackend

                self.backend = OutlinesBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            elif backend == "lm-format-enforcer":
                from vllm.v1.structured_output.backend_lm_format_enforcer import (  # noqa: E501
                    LMFormatEnforcerBackend,
                )

                self.backend = LMFormatEnforcerBackend(
                    self.vllm_config,
                    tokenizer=self.tokenizer,
                    vocab_size=vocab_size,
                )
            else:
                raise ValueError(f"Unsupported structured output backend: {backend}")

        if self._use_async_grammar_compilation:
            grammar = self.executor.submit(self._create_grammar, request)
        else:
            grammar = self._create_grammar(request)  # type: ignore[assignment]
        request.structured_output_request.grammar = grammar