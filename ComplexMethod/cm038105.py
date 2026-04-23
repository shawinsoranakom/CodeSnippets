def get_generation_prompt(cls, stt_params: SpeechToTextParams) -> PromptType:
        """
        Construct a transcription/translation prompt for Qwen3-Omni.
        """
        audio = stt_params.audio
        stt_config = stt_params.stt_config
        model_config = stt_params.model_config
        language = stt_params.language
        task_type = stt_params.task_type
        to_language = stt_params.to_language
        request_prompt = stt_params.request_prompt
        # Transcribe this audio [into <language>] | for transcription
        # Translate this audio [from <language> into <to_language>] | for translation
        instruction = "Transcribe" if task_type == "transcribe" else "Translate"
        instruction += " this audio"

        # Default to_language to English for translation
        if task_type == "translate" and to_language is None:
            to_language = "en"

        # Get full language names from supported_languages mapping
        full_lang_name = cls.supported_languages.get(language, "")
        full_lang_name_to = cls.supported_languages.get(to_language, "")

        if task_type == "transcribe" and full_lang_name:
            instruction += f" into {full_lang_name}"
        elif task_type == "translate":
            if full_lang_name:
                instruction += f" from {full_lang_name}"
            if full_lang_name_to:
                instruction += f" into {full_lang_name_to}"

        instruction += "."

        if request_prompt:
            instruction += f" {request_prompt}"

        processor = cached_processor_from_config(
            model_config, processor_cls=Qwen3OmniMoeProcessor
        )
        # Audio placeholder format: <|audio_start|><|audio_pad|><|audio_end|>
        audio_placeholder = "<|audio_start|><|audio_pad|><|audio_end|>"
        user_content = f"{audio_placeholder}{instruction}"

        messages = [{"role": "user", "content": user_content}]
        prompt = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        audio_data = (audio, stt_config.sample_rate)
        prompts_dict = {"multi_modal_data": {"audio": audio_data}, "prompt": prompt}
        return cast(PromptType, prompts_dict)