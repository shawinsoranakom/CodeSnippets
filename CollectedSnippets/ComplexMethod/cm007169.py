def build_model(self) -> LanguageModel:
        task = self.task or None
        huggingfacehub_api_token = self.huggingfacehub_api_token
        model_kwargs = self.model_kwargs or {}
        max_new_tokens = self.max_new_tokens
        top_k = self.top_k or None
        top_p = self.top_p
        typical_p = self.typical_p or None
        temperature = self.temperature or 0.8
        repetition_penalty = self.repetition_penalty or None

        try:
            llm = self.create_huggingface_endpoint(
                task=task,
                huggingfacehub_api_token=huggingfacehub_api_token,
                model_kwargs=model_kwargs,
                max_new_tokens=max_new_tokens,
                top_k=top_k,
                top_p=top_p,
                typical_p=typical_p,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
            )
        except Exception as e:
            msg = "Could not connect to Hugging Face Endpoints API."
            raise ValueError(msg) from e

        return llm