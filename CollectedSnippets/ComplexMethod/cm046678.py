def pre_detect_and_load_tokenizer(
        self,
        model_name: str,
        max_seq_length: int = 2048,
        hf_token: Optional[str] = None,
        is_dataset_image: bool = False,
        is_dataset_audio: bool = False,
        trust_remote_code: bool = False,
    ) -> None:
        """Lightweight detection and tokenizer load — no model weights, no VRAM.

        Sets is_vlm, _audio_type, is_audio_vlm, model_name and loads a
        lightweight tokenizer for dataset formatting.  Call this before
        load_and_format_dataset() when you want to process the dataset
        BEFORE loading the training model (avoids VRAM contention with
        the LLM-assisted detection helper).

        load_model() may be called afterwards — it will re-detect and load
        the full model + tokenizer, overwriting the lightweight one set here.
        """
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.trust_remote_code = trust_remote_code

        if hf_token:
            os.environ["HF_TOKEN"] = hf_token

        # --- Detect audio type (reads config.json only, no VRAM) ---
        self._audio_type = detect_audio_type(model_name, hf_token)
        if self._audio_type == "audio_vlm":
            self.is_audio = False
            self.is_audio_vlm = is_dataset_audio
            self._audio_type = None
        else:
            self.is_audio = self._audio_type is not None
            self.is_audio_vlm = False

        if not self.is_audio and not self.is_audio_vlm:
            self._cuda_audio_used = False

        # --- Detect VLM ---
        vision = (
            is_vision_model(model_name, hf_token = hf_token)
            if not self.is_audio
            else False
        )
        self.is_vlm = not self.is_audio_vlm and vision and is_dataset_image

        logger.info(
            "pre_detect: audio_type=%s, is_audio=%s, is_audio_vlm=%s, is_vlm=%s",
            self._audio_type,
            self.is_audio,
            self.is_audio_vlm,
            self.is_vlm,
        )

        # --- Load lightweight tokenizer/processor (CPU only, no VRAM) ---
        # Whisper needs AutoProcessor (has feature_extractor + tokenizer).
        # All others work with AutoTokenizer (CSM loads its own processor inline).
        if self._audio_type == "whisper":
            from transformers import AutoProcessor

            self.tokenizer = AutoProcessor.from_pretrained(
                model_name,
                trust_remote_code = trust_remote_code,
                token = hf_token,
            )
        else:
            from transformers import AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code = trust_remote_code,
                token = hf_token,
            )

        logger.info("Pre-loaded tokenizer for %s", model_name)