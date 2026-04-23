def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        for field_name in ("model", "repo_id"):
            value = getattr(self, field_name)
            if value and value.startswith(("http://", "https://")):
                msg = f"`{field_name}` must be a HuggingFace repo ID, not a URL."
                raise ValueError(msg)

        huggingfacehub_api_token = self.huggingfacehub_api_token or os.getenv(
            "HF_TOKEN"
        )

        try:
            from huggingface_hub import (  # type: ignore[import]
                AsyncInferenceClient,
                InferenceClient,
            )

            if self.model:
                self.repo_id = self.model
            elif self.repo_id:
                self.model = self.repo_id
            else:
                self.model = DEFAULT_MODEL
                self.repo_id = DEFAULT_MODEL

            client = InferenceClient(
                model=self.model,
                token=huggingfacehub_api_token,
                provider=self.provider,  # type: ignore[arg-type]
            )

            async_client = AsyncInferenceClient(
                model=self.model,
                token=huggingfacehub_api_token,
                provider=self.provider,  # type: ignore[arg-type]
            )

            if self.task not in VALID_TASKS:
                msg = (
                    f"Got invalid task {self.task}, "
                    f"currently only {VALID_TASKS} are supported"
                )
                raise ValueError(msg)
            self.client = client
            self.async_client = async_client

        except ImportError as e:
            msg = (
                "Could not import huggingface_hub python package. "
                "Please install it with `pip install huggingface_hub`."
            )
            raise ImportError(msg) from e
        return self