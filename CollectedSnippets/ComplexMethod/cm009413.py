def _resolve_model_id(self) -> None:
        """Resolve the model_id from the LLM's inference_server_url."""
        from huggingface_hub import list_inference_endpoints  # type: ignore[import]

        if _is_huggingface_hub(self.llm) or (
            hasattr(self.llm, "repo_id") and self.llm.repo_id
        ):
            self.model_id = self.llm.repo_id
            return
        if _is_huggingface_textgen_inference(self.llm):
            endpoint_url: str | None = self.llm.inference_server_url
        if _is_huggingface_pipeline(self.llm):
            from transformers import AutoTokenizer  # type: ignore[import]

            self.model_id = self.model_id or self.llm.model_id
            self.tokenizer = (
                AutoTokenizer.from_pretrained(self.model_id)
                if self.tokenizer is None
                else self.tokenizer
            )
            return
        if _is_huggingface_endpoint(self.llm):
            self.model_id = self.llm.repo_id or self.llm.model
            return
        endpoint_url = self.llm.endpoint_url
        available_endpoints = list_inference_endpoints("*")
        for endpoint in available_endpoints:
            if endpoint.url == endpoint_url:
                self.model_id = endpoint.repository

        if not self.model_id:
            msg = (
                "Failed to resolve model_id:"
                f"Could not find model id for inference server: {endpoint_url}"
                "Make sure that your Hugging Face token has access to the endpoint."
            )
            raise ValueError(msg)