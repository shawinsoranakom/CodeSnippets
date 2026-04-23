def generate_audio_response(
        self,
        text: str,
        temperature: float = 0.6,
        top_p: float = 0.95,
        top_k: int = 50,
        min_p: float = 0.0,
        max_new_tokens: int = 2048,
        repetition_penalty: float = 1.0,
        use_adapter: Optional[Union[bool, str]] = None,
    ) -> Tuple[bytes, int]:
        """
        Generate audio from text for TTS models.
        Returns (wav_bytes, sample_rate).
        Blocking — generates complete audio before returning.
        """
        if not self.active_model_name:
            raise RuntimeError("No active model")

        model_info = self.models[self.active_model_name]
        audio_type = model_info.get("audio_type")
        model = model_info["model"]
        tokenizer = model_info.get("tokenizer")

        if not audio_type:
            raise RuntimeError(f"Model {self.active_model_name} is not an audio model")

        top_k = self._normalize_top_k(top_k)

        with self._generation_lock:
            if use_adapter is not None:
                self._apply_adapter_state(use_adapter)

            if audio_type == "snac":
                return self._generate_snac(
                    model,
                    tokenizer,
                    text,
                    temperature,
                    top_p,
                    max_new_tokens,
                    repetition_penalty,
                )
            elif audio_type == "csm":
                processor = model_info.get("processor", tokenizer)
                return self._generate_csm(model, processor, text, max_new_tokens)
            elif audio_type == "bicodec":
                return self._generate_bicodec(
                    model, tokenizer, text, temperature, top_k, max_new_tokens
                )
            elif audio_type == "dac":
                return self._generate_dac(
                    model,
                    tokenizer,
                    text,
                    temperature,
                    top_k,
                    top_p,
                    min_p,
                    max_new_tokens,
                    repetition_penalty,
                )
            else:
                raise RuntimeError(f"Unknown audio_type: {audio_type}")