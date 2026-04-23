def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        try:
            import litellm

            litellm.drop_params = True
            litellm.set_verbose = self.verbose
        except ImportError as e:
            msg = "Could not import litellm python package. Please install it with `pip install litellm`"
            raise ChatLiteLLMException(msg) from e
        # Remove empty keys
        if "" in self.kwargs:
            del self.kwargs[""]
        if "" in self.model_kwargs:
            del self.model_kwargs[""]
        # Report missing fields for Azure provider
        if self.provider == "Azure":
            if "api_base" not in self.kwargs:
                msg = "Missing api_base on kwargs"
                raise ValueError(msg)
            if "api_version" not in self.model_kwargs:
                msg = "Missing api_version on model_kwargs"
                raise ValueError(msg)
        output = ChatLiteLLM(
            model=f"{self.provider.lower()}/{self.model}",
            client=None,
            streaming=self.stream,
            temperature=self.temperature,
            model_kwargs=self.model_kwargs if self.model_kwargs is not None else {},
            top_p=self.top_p,
            top_k=self.top_k,
            n=self.n,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
            **self.kwargs,
        )
        output.client.api_key = self.api_key

        return output