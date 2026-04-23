def _chat_params(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Assemble the parameters for a chat completion request.

        Args:
            messages: List of LangChain messages to send to the model.
            stop: Optional list of stop tokens to use for this invocation.
            **kwargs: Additional keyword arguments to include in the request.

        Returns:
            A dictionary of parameters to pass to the Ollama client.
        """
        ollama_messages = self._convert_messages_to_ollama_messages(messages)

        if self.stop is not None and stop is not None:
            msg = "`stop` found in both the input and default params."
            raise ValueError(msg)
        if self.stop is not None:
            stop = self.stop

        options_dict = kwargs.pop("options", None)
        if options_dict is None:
            # Only include parameters that are explicitly set (not None)
            options_dict = {
                k: v
                for k, v in {
                    "mirostat": self.mirostat,
                    "mirostat_eta": self.mirostat_eta,
                    "mirostat_tau": self.mirostat_tau,
                    "num_ctx": self.num_ctx,
                    "num_gpu": self.num_gpu,
                    "num_thread": self.num_thread,
                    "num_predict": self.num_predict,
                    "repeat_last_n": self.repeat_last_n,
                    "repeat_penalty": self.repeat_penalty,
                    "temperature": self.temperature,
                    "seed": self.seed,
                    "stop": self.stop if stop is None else stop,
                    "tfs_z": self.tfs_z,
                    "top_k": self.top_k,
                    "top_p": self.top_p,
                }.items()
                if v is not None
            }

        format_param = self._resolve_format_param(
            kwargs.pop("format", self.format),
            kwargs.pop("response_format", None),
        )

        params = {
            "messages": ollama_messages,
            "stream": kwargs.pop("stream", True),
            "model": kwargs.pop("model", self.model),
            "think": kwargs.pop("reasoning", self.reasoning),
            "format": format_param,
            "logprobs": kwargs.pop("logprobs", self.logprobs),
            "top_logprobs": kwargs.pop("top_logprobs", self.top_logprobs),
            "options": options_dict,
            "keep_alive": kwargs.pop("keep_alive", self.keep_alive),
            **kwargs,
        }

        # Filter out 'strict' argument if present, as it is not supported by Ollama
        # but may be passed by upstream libraries (e.g. LangChain ProviderStrategy)
        if "strict" in params:
            params.pop("strict")

        if tools := kwargs.get("tools"):
            params["tools"] = tools

        return params