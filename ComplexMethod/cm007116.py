def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        # Mapping mirostat settings to their corresponding values
        mirostat_options = {"Mirostat": 1, "Mirostat 2.0": 2}

        # Default to None for 'Disabled'
        mirostat_value = mirostat_options.get(self.mirostat, None)

        # Set mirostat_eta and mirostat_tau to None if mirostat is disabled
        if mirostat_value is None:
            mirostat_eta = None
            mirostat_tau = None
        else:
            mirostat_eta = self.mirostat_eta
            mirostat_tau = self.mirostat_tau

        transformed_base_url = transform_localhost_url(self.base_url)

        # Check if URL contains /v1 suffix (OpenAI-compatible mode)
        if transformed_base_url and transformed_base_url.rstrip("/").endswith("/v1"):
            # Strip /v1 suffix and log warning
            transformed_base_url = transformed_base_url.rstrip("/").removesuffix("/v1")
            logger.warning(
                "Detected '/v1' suffix in base URL. The Ollama component uses the native Ollama API, "
                "not the OpenAI-compatible API. The '/v1' suffix has been automatically removed. "
                "If you want to use the OpenAI-compatible API, please use the OpenAI component instead. "
                "Learn more at https://docs.ollama.com/openai#openai-compatibility"
            )

        try:
            output_format = self._parse_format_field(self.format) if self.enable_structured_output else None
        except Exception as e:
            msg = f"Failed to parse the format field: {e}"
            raise ValueError(msg) from e

        # Mapping system settings to their corresponding values
        llm_params = {
            "base_url": transformed_base_url,
            "model": self.model_name,
            "mirostat": mirostat_value,
            "format": output_format or None,
            "metadata": self.metadata,
            "tags": self.tags.split(",") if self.tags else None,
            "mirostat_eta": mirostat_eta,
            "mirostat_tau": mirostat_tau,
            "num_ctx": self.num_ctx or None,
            "num_gpu": self.num_gpu or None,
            "num_thread": self.num_thread or None,
            "repeat_last_n": self.repeat_last_n or None,
            "repeat_penalty": self.repeat_penalty or None,
            "temperature": self.temperature or None,
            "stop": self.stop_tokens.split(",") if self.stop_tokens else None,
            "system": self.system,
            "tfs_z": self.tfs_z or None,
            "timeout": self.timeout or None,
            "top_k": self.top_k or None,
            "top_p": self.top_p or None,
            "verbose": self.enable_verbose_output or False,
            "template": self.template,
        }
        headers = self.headers
        if headers is not None:
            llm_params["client_kwargs"] = {"headers": headers}

        # Remove parameters with None values
        llm_params = {k: v for k, v in llm_params.items() if v is not None}

        try:
            output = ChatOllama(**llm_params)
        except Exception as e:
            msg = (
                "Unable to connect to the Ollama API. "
                "Please verify the base URL, ensure the relevant Ollama model is pulled, and try again."
            )
            raise ValueError(msg) from e

        return output