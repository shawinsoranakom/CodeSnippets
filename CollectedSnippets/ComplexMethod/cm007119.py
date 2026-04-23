def build_model(self) -> LanguageModel:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            msg = "langchain-openai not installed. Please install with `pip install langchain-openai`"
            raise ImportError(msg) from e

        api_key = SecretStr(self.api_key).get_secret_value() if self.api_key else None
        output = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature if self.temperature is not None else 0.1,
            max_tokens=self.max_tokens or None,
            model_kwargs=self.model_kwargs or {},
            base_url=self.api_base,
            api_key=api_key,
            streaming=self.stream if hasattr(self, "stream") else False,
            seed=self.seed,
        )

        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output