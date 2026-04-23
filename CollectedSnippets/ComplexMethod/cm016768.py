def tokenize_with_weights(self, text, return_word_ids=False, **kwargs):
        text = text.strip()
        text_negative = kwargs.get("caption_negative", text).strip()
        lyrics = kwargs.get("lyrics", "")
        lyrics_negative = kwargs.get("lyrics_negative", lyrics)
        duration = kwargs.get("duration", 120)
        if isinstance(duration, str):
            duration = float(duration.split(None, 1)[0])
        language = kwargs.get("language")
        seed = kwargs.get("seed", 0)

        generate_audio_codes = kwargs.get("generate_audio_codes", True)
        cfg_scale = kwargs.get("cfg_scale", 2.0)
        temperature = kwargs.get("temperature", 0.85)
        top_p = kwargs.get("top_p", 0.9)
        top_k = kwargs.get("top_k", 0.0)
        min_p = kwargs.get("min_p", 0.000)

        duration = math.ceil(duration)
        kwargs["duration"] = duration
        tokens_duration = duration * 5
        min_tokens = int(kwargs.get("min_tokens", tokens_duration))
        max_tokens = int(kwargs.get("max_tokens", tokens_duration))

        metas_negative = {
            k.rsplit("_", 1)[0]: kwargs.pop(k)
            for k in ("bpm_negative", "duration_negative", "keyscale_negative", "timesignature_negative", "language_negative", "caption_negative")
            if k in kwargs
        }
        if not kwargs.get("use_negative_caption"):
            _ = metas_negative.pop("caption", None)

        cot_text = self._metas_to_cot(caption=text, **kwargs)
        cot_text_negative = "<think>\n\n</think>" if not metas_negative else self._metas_to_cot(**metas_negative)
        meta_cap = self._metas_to_cap(**kwargs)

        lm_template = "<|im_start|>system\n# Instruction\nGenerate audio semantic tokens based on the given conditions:\n\n<|im_end|>\n<|im_start|>user\n# Caption\n{}\n\n# Lyric\n{}\n<|im_end|>\n<|im_start|>assistant\n{}\n\n<|im_end|>\n"
        lyrics_template = "# Languages\n{}\n\n# Lyric\n{}<|endoftext|><|endoftext|>"
        qwen3_06b_template = "# Instruction\nGenerate audio semantic tokens based on the given conditions:\n\n# Caption\n{}\n\n# Metas\n{}\n<|endoftext|>\n<|endoftext|>"

        llm_prompts = {
            "lm_prompt": lm_template.format(text, lyrics.strip(), cot_text),
            "lm_prompt_negative": lm_template.format(text_negative, lyrics_negative.strip(), cot_text_negative),
            "lyrics": lyrics_template.format(language if language is not None else "", lyrics),
            "qwen3_06b": qwen3_06b_template.format(text, meta_cap),
        }

        out = {
            prompt_key: self.qwen3_06b.tokenize_with_weights(
                prompt,
                prompt_key == "qwen3_06b" and return_word_ids,
                disable_weights = True,
                **kwargs,
            )
            for prompt_key, prompt in llm_prompts.items()
        }
        out["lm_metadata"] = {"min_tokens": min_tokens,
                              "max_tokens": max_tokens,
                              "seed": seed,
                              "generate_audio_codes": generate_audio_codes,
                              "cfg_scale": cfg_scale,
                              "temperature": temperature,
                              "top_p": top_p,
                              "top_k": top_k,
                              "min_p": min_p,
                              }
        return out