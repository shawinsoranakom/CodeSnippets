def generate(
        self,
        input_ids: torch.Tensor | None = None,
        history_prompt: dict[str, torch.Tensor] | None = None,
        return_output_lengths: bool | None = None,
        **kwargs,
    ) -> torch.LongTensor:
        """
        Generates audio from an input prompt and an additional optional `Bark` speaker prompt.

        Args:
            input_ids (`Optional[torch.Tensor]` of shape (batch_size, seq_len), *optional*):
                Input ids. Will be truncated up to 256 tokens. Note that the output audios will be as long as the
                longest generation among the batch.
            history_prompt (`Optional[dict[str,torch.Tensor]]`, *optional*):
                Optional `Bark` speaker prompt. Note that for now, this model takes only one speaker prompt per batch.
            kwargs (*optional*): Remaining dictionary of keyword arguments. Keyword arguments are of two types:

                - Without a prefix, they will be entered as `**kwargs` for the `generate` method of each sub-model.
                - With a *semantic_*, *coarse_*, *fine_* prefix, they will be input for the `generate` method of the
                semantic, coarse and fine respectively. It has the priority over the keywords without a prefix.

                This means you can, for example, specify a generation strategy for all sub-models except one.
            return_output_lengths (`bool`, *optional*):
                Whether or not to return the waveform lengths. Useful when batching.
        Returns:
            By default:
                - **audio_waveform** (`torch.Tensor` of shape (batch_size, seq_len)): Generated audio waveform.
            When `return_output_lengths=True`:
                Returns a tuple made of:
                - **audio_waveform** (`torch.Tensor` of shape (batch_size, seq_len)): Generated audio waveform.
                - **output_lengths** (`torch.Tensor` of shape (batch_size)): The length of each waveform in the batch
        Example:

        ```python
        >>> from transformers import AutoProcessor, BarkModel

        >>> processor = AutoProcessor.from_pretrained("suno/bark-small")
        >>> model = BarkModel.from_pretrained("suno/bark-small")

        >>> # To add a voice preset, you can pass `voice_preset` to `BarkProcessor.__call__(...)`
        >>> voice_preset = "v2/en_speaker_6"

        >>> inputs = processor("Hello, my dog is cute, I need him in my life", voice_preset=voice_preset)

        >>> audio_array = model.generate(**inputs, semantic_max_new_tokens=100)
        >>> audio_array = audio_array.cpu().numpy().squeeze()
        ```
        """
        # TODO (joao):workaround until nested generation config is compatible with PreTrained Model
        # todo: dict
        semantic_generation_config = BarkSemanticGenerationConfig(**self.generation_config.semantic_config)
        coarse_generation_config = BarkCoarseGenerationConfig(**self.generation_config.coarse_acoustics_config)
        fine_generation_config = BarkFineGenerationConfig(**self.generation_config.fine_acoustics_config)

        kwargs_semantic = {
            # if "attention_mask" is set, it should not be passed to CoarseModel and FineModel
            "attention_mask": kwargs.pop("attention_mask", None),
            "min_eos_p": kwargs.pop("min_eos_p", None),
        }
        kwargs_coarse = {}
        kwargs_fine = {}
        for key, value in kwargs.items():
            if key.startswith("semantic_"):
                key = key[len("semantic_") :]
                kwargs_semantic[key] = value
            elif key.startswith("coarse_"):
                key = key[len("coarse_") :]
                kwargs_coarse[key] = value
            elif key.startswith("fine_"):
                key = key[len("fine_") :]
                kwargs_fine[key] = value
            else:
                # If the key is already in a specific config, then it's been set with a
                # submodules specific value and we don't override
                if key not in kwargs_semantic:
                    kwargs_semantic[key] = value
                if key not in kwargs_coarse:
                    kwargs_coarse[key] = value
                if key not in kwargs_fine:
                    kwargs_fine[key] = value

        # 1. Generate from the semantic model
        if "generation_config" in kwargs_semantic:
            kwargs_semantic.pop("generation_config")
        semantic_output = self.semantic.generate(
            input_ids,
            history_prompt=history_prompt,
            semantic_generation_config=semantic_generation_config,
            **kwargs_semantic,
        )

        # 2. Generate from the coarse model
        if "generation_config" in kwargs_coarse:
            kwargs_coarse.pop("generation_config")
        coarse_output = self.coarse_acoustics.generate(
            semantic_output,
            history_prompt=history_prompt,
            semantic_generation_config=semantic_generation_config,
            coarse_generation_config=coarse_generation_config,
            codebook_size=self.generation_config.codebook_size,
            return_output_lengths=return_output_lengths,
            **kwargs_coarse,
        )

        output_lengths = None
        if return_output_lengths:
            coarse_output, output_lengths = coarse_output
            # (batch_size, seq_len*coarse_codebooks) -> (batch_size, seq_len)
            output_lengths = output_lengths // coarse_generation_config.n_coarse_codebooks

        # 3. "generate" from the fine model
        if "generation_config" in kwargs_fine:
            kwargs_fine.pop("generation_config")
        output = self.fine_acoustics.generate(
            coarse_output,
            history_prompt=history_prompt,
            semantic_generation_config=semantic_generation_config,
            coarse_generation_config=coarse_generation_config,
            fine_generation_config=fine_generation_config,
            codebook_size=self.generation_config.codebook_size,
            **kwargs_fine,
        )

        if getattr(self, "fine_acoustics_hook", None) is not None:
            # Manually offload fine_acoustics to CPU
            # and load codec_model to GPU
            # since bark doesn't use codec_model forward pass
            self.fine_acoustics_hook.offload()
            self.codec_model = self.codec_model.to(self.device)

        # 4. Decode the output and generate audio array
        audio = self.codec_decode(output, output_lengths)

        if getattr(self, "codec_model_hook", None) is not None:
            # Offload codec_model to CPU
            self.codec_model_hook.offload()

        if return_output_lengths:
            output_lengths = [len(sample) for sample in audio]
            audio = nn.utils.rnn.pad_sequence(audio, batch_first=True, padding_value=0)
            return audio, output_lengths

        return audio