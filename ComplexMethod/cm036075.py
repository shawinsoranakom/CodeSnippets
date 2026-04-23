def get_inputs(
        self,
        prompts: list[str]
        | list[torch.Tensor]
        | list[list[int]]
        | list[dict[str, Any]],
        images: PromptImageInput | None = None,
        videos: PromptVideoInput | None = None,
        audios: PromptAudioInput | None = None,
    ) -> list[dict[str, Any]]:
        if any(
            x is not None and len(x) != len(prompts) for x in [images, videos, audios]
        ):
            raise ValueError(
                "All non-None multimodal inputs must have the same length as prompts"
            )

        inputs = list[dict[str, Any]]()
        for i, prompt in enumerate(prompts):
            # If we're passing an encoder/decoder prompt, we assume it
            # already contains the multimodal data in the prompt
            if isinstance(prompt, dict):
                assert images is None and audios is None and videos is None
                inputs.append(prompt.copy())
            else:
                prompt_dict = dict[str, Any]()
                if isinstance(prompt, str):
                    prompt_dict["prompt"] = prompt
                elif isinstance(prompt, list):
                    prompt_dict["prompt_token_ids"] = prompt
                else:
                    prompt_dict["prompt_embeds"] = prompt

                multi_modal_data = dict[str, Any]()
                if images is not None and (image := images[i]) is not None:
                    multi_modal_data["image"] = image
                if videos is not None and (video := videos[i]) is not None:
                    multi_modal_data["video"] = video
                if audios is not None and (audio := audios[i]) is not None:
                    multi_modal_data["audio"] = audio

                if multi_modal_data:
                    prompt_dict["multi_modal_data"] = multi_modal_data

                inputs.append(prompt_dict)

        return inputs