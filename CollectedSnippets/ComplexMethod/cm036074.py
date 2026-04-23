def get_inputs(
        self,
        prompts: list[str] | list[list[int]],
        images: PromptImageInput | None = None,
        videos: PromptVideoInput | None = None,
        audios: PromptAudioInput | None = None,
        tokenization_kwargs: dict[str, Any] | None = None,
    ) -> list[BatchFeature | BatchEncoding | dict[str, torch.Tensor]]:
        if images is not None:
            assert len(prompts) == len(images)

        if videos is not None:
            assert len(prompts) == len(videos)

        if audios is not None:
            assert len(prompts) == len(audios)

        all_inputs: list[BatchFeature | BatchEncoding | dict[str, torch.Tensor]] = []
        for i, prompt in enumerate(prompts):
            if isinstance(prompt, str):
                # Create a copy to avoid modifying the original dict
                processor_kwargs = (
                    tokenization_kwargs.copy()
                    if tokenization_kwargs is not None
                    else {}
                )
                processor_kwargs.update(
                    {
                        "text": prompt,
                        "return_tensors": "pt",
                    }
                )
                if images is not None and (image := images[i]) is not None:
                    processor_kwargs["images"] = image
                if videos is not None and (video := videos[i]) is not None:
                    processor_kwargs["videos"] = video
                if audios is not None and (audio_inputs := audios[i]) is not None:
                    # HACK - not all processors take sampling_rate; we should
                    # clean this up in the future.
                    if len(audio_inputs) == 2:
                        audio, sr = audio_inputs
                        processor_kwargs["audio"] = audio
                        processor_kwargs["sampling_rate"] = sr
                    else:
                        processor_kwargs["audio"] = audio_inputs

                inputs = self.processor(**processor_kwargs)
                if isinstance(inputs, BatchFeature):
                    inputs = inputs.to(dtype=self.dtype)
                all_inputs.append(inputs)
            else:
                # check that prompt is (batched) list of integers (token ids)
                if not is_list_of(prompt, typ=int, check="all"):
                    raise ValueError(
                        "Prompt must be a list of ints corresponding to the prompt token ids."
                    )
                # check that no multimodal input is provided
                if images or videos or audios:
                    raise ValueError(
                        "When providing prompt token ids multimodal inputs are not supported."
                    )
                input_dict = {
                    "input_ids": torch.tensor(prompt, dtype=torch.long).unsqueeze(0),
                }
                all_inputs.append(input_dict)

        return all_inputs