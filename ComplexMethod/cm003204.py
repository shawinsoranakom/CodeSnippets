def __call__(
        self,
        images: ImageInput | list[ImageInput] | list[list[ImageInput]] | None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        actions: list | np.ndarray | torch.Tensor | None = None,
        state: list | np.ndarray | torch.Tensor | None = None,
        **kwargs: Unpack[PI0ProcessorKwargs],
    ) -> BatchFeature:
        r"""
        actions (`list | np.ndarray | torch.Tensor`, *optional*):
            Actions to be predicted by the model. If provided, padding, mean and std normalization will be applied.
        state (`list | np.ndarray | torch.Tensor`, *optional*):
            Robotic states to be predicted by the model. If provided, padding, mean and std normalization will be applied.

        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`. If `suffix`
              is provided, the `input_ids` will also contain the suffix input ids.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
            - **pixel_attention_mask** -- Pixel values padding mask to be fed to a model. Returned when `images` is not `None`.
            - **state** -- Robot state compatible with model if `state` is not None
            - **actions** -- Label-actions compatible with training if `actions` is not None
        """
        output_kwargs = self._merge_kwargs(
            PI0ProcessorKwargs, tokenizer_init_kwargs=self.tokenizer.init_kwargs, **kwargs
        )

        if text is None:
            logger.warning_once("You are using PI0 without a text prefix. The processor will use an empty prompt.")
            text = ""

        if isinstance(text, str):
            text = [text]

        batched_images = make_nested_list_of_images(images)
        if len(batched_images) != len(text):
            raise ValueError(
                f"Received {len(batched_images)} image samples for {len(text)} prompts. "
                "Each prompt should be associated with one sample (with one or more camera images)."
            )

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        output_kwargs["images_kwargs"].pop("return_tensors", None)

        prompt_strings = []
        for sample, image_list in zip(text, batched_images):
            sample = (
                f"{self.image_token * self.image_seq_length * len(image_list)}{self.tokenizer.bos_token}{sample}\n"
            )
            prompt_strings.append(sample)

        text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"])

        # Here is the diff from PaliGemma. Ideally we'd create a new ImageProcessor if it were a VLM
        max_num_cameras = max(len(sample_images) for sample_images in batched_images)
        pixel_attention_mask = torch.zeros((len(batched_images), max_num_cameras), dtype=torch.bool)
        padded_pixel_values = torch.zeros(len(batched_images), max_num_cameras, 3, self.height, self.width)

        for batch, sample_images in enumerate(batched_images):
            processed = self.image_processor(sample_images, return_tensors="pt", **output_kwargs["images_kwargs"])

            num_cameras = len(sample_images)
            pixel_attention_mask[batch, :num_cameras] = True
            padded_pixel_values[batch, :num_cameras] = processed["pixel_values"]

        return_data = {
            **text_inputs,
            "pixel_values": padded_pixel_values,
            "pixel_attention_mask": pixel_attention_mask,
        }

        if actions is not None:
            actions = (torch.tensor(actions) - self.actions_mean) / (self.actions_std + 1e-08)
            if actions.shape[-1] < self.max_state_dim:
                actions = F.pad(actions, (0, self.max_state_dim - actions.shape[-1]))
            return_data["actions"] = actions.view(-1, self.chunk_size, self.max_state_dim)

        if state is not None:
            state = (torch.tensor(state) - self.state_mean) / (self.state_std + 1e-08)
            if state.shape[-1] < self.max_state_dim:
                state = F.pad(state, (0, self.max_state_dim - state.shape[-1]))
            return_data["state"] = state.view(-1, self.max_state_dim)

        return BatchFeature(data=return_data, tensor_type=return_tensors)