def _inherit_llm_properties(self) -> None:
        """Inherit properties from the wrapped LLM instance if not explicitly set."""
        if not hasattr(self, "llm") or self.llm is None:
            return

        # Map of ChatHuggingFace properties to LLM properties
        property_mappings = {
            "temperature": "temperature",
            "max_tokens": "max_new_tokens",  # Different naming convention
            "top_p": "top_p",
            "seed": "seed",
            "streaming": "streaming",
            "stop": "stop_sequences",
        }

        # Inherit properties from LLM and not explicitly set here
        for chat_prop, llm_prop in property_mappings.items():
            if hasattr(self.llm, llm_prop):
                llm_value = getattr(self.llm, llm_prop)
                chat_value = getattr(self, chat_prop, None)
                if not chat_value and llm_value:
                    setattr(self, chat_prop, llm_value)

        # Handle special cases for HuggingFaceEndpoint
        if _is_huggingface_endpoint(self.llm):
            # Inherit additional HuggingFaceEndpoint specific properties
            endpoint_mappings = {
                "frequency_penalty": "repetition_penalty",
            }

            for chat_prop, llm_prop in endpoint_mappings.items():
                if hasattr(self.llm, llm_prop):
                    llm_value = getattr(self.llm, llm_prop)
                    chat_value = getattr(self, chat_prop, None)
                    if chat_value is None and llm_value is not None:
                        setattr(self, chat_prop, llm_value)

        # Inherit model_kwargs if not explicitly set
        if (
            not self.model_kwargs
            and hasattr(self.llm, "model_kwargs")
            and isinstance(self.llm.model_kwargs, dict)
        ):
            self.model_kwargs = self.llm.model_kwargs.copy()