def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        pixel_values: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = None,
        interpolate_pos_encoding: bool = False,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | BaseModelOutputWithPooling:
        r"""
        Examples:

        ```python
        >>> from transformers import AutoProcessor, AutoModel
        >>> import httpx
        >>> from io import BytesIO
        >>> from PIL import Image

        >>> processor = AutoProcessor.from_pretrained("microsoft/git-base")
        >>> model = AutoModel.from_pretrained("microsoft/git-base")

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> text = "this is an image of two cats"

        >>> inputs = processor(images=image, text=text, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> last_hidden_state = outputs.last_hidden_state
        ```"""
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        # past_key_values_length
        past_key_values_length = 0
        if past_key_values is not None:
            past_key_values_length = (
                past_key_values.get_seq_length()
                if not isinstance(past_key_values, Cache)
                else past_key_values.get_seq_length()
            )

        # Adjust position ids by adding image seq length
        if pixel_values is None and past_key_values is not None and input_ids.shape[1] == 1:
            position_ids = position_ids + past_key_values_length

        embedding_output = self.embeddings(
            input_ids=input_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            past_key_values_length=past_key_values_length,
        )

        # Always create `token_type_ids` so we can re-use Gemma3 style mask preparation fn
        token_type_ids = torch.zeros_like(embedding_output, dtype=torch.int)[..., 0]

        if pixel_values is not None:
            if pixel_values.ndim == 4:
                # here we assume pixel_values is of shape (batch_size, num_channels, height, width)
                visual_features = self.image_encoder(
                    pixel_values, interpolate_pos_encoding=interpolate_pos_encoding
                ).last_hidden_state

            elif pixel_values.ndim == 5:
                # here we assume pixel_values is of shape (batch_size, num_frames, num_channels, height, width)
                visual_features = []
                for frame_idx in range(pixel_values.shape[1]):
                    visual_features_frame = self.image_encoder(
                        pixel_values[:, frame_idx, :, :], interpolate_pos_encoding=interpolate_pos_encoding
                    ).last_hidden_state
                    visual_features_frame += self.img_temporal_embedding[frame_idx]
                    visual_features.append(visual_features_frame)

                # finally, concatenate all features along sequence dimension
                visual_features = torch.cat(visual_features, dim=1)

            else:
                raise ValueError("pixel_values must be of rank 4 or 5")

            projected_visual_features = self.visual_projection(visual_features)

            # Repeat visual features to match embedding batch size.
            projected_visual_features = projected_visual_features.repeat(
                embedding_output.size(0) // projected_visual_features.size(0), 1, 1
            )

            # concatenate patch token and text token embeddings
            embedding_output = torch.cat((projected_visual_features, embedding_output), dim=1)
            image_token_type_ids = torch.ones_like(projected_visual_features, dtype=torch.int)[..., 0]
            token_type_ids = torch.cat([image_token_type_ids, token_type_ids], dim=-1)
            if attention_mask is not None:
                attention_mask = torch.cat([torch.ones_like(image_token_type_ids), attention_mask], dim=-1)
        elif past_key_values is not None and input_ids.shape[1] == 1:
            # Expand attention mask and cache position with image tokens because GIT doesn't add image
            # placeholder tokens when processing. Doesn't worth the refactor, low usage!
            extended_attention_mask = torch.ones(
                (attention_mask.shape[0], past_key_values_length - attention_mask.shape[1] + 1),
                dtype=attention_mask.dtype,
                device=attention_mask.device,
            )
            attention_mask = torch.cat([extended_attention_mask, attention_mask], dim=-1)

        # Images attend each other bidirectionally while text remains causal
        causal_mask = create_causal_mask_mapping(
            self.config,
            inputs_embeds=embedding_output,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=None,
            token_type_ids=token_type_ids,
        )

        hidden_states = embedding_output

        encoder_outputs: BaseModelOutputWithPast = self.encoder(
            hidden_states,
            attention_mask=causal_mask,
            past_key_values=past_key_values,
            use_cache=use_cache,
            **kwargs,
        )

        return BaseModelOutputWithPast(
            last_hidden_state=encoder_outputs.last_hidden_state,
            past_key_values=encoder_outputs.past_key_values,
        )