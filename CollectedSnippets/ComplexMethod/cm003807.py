def forward(
        self,
        pixel_values: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> BaseModelOutputWithPooling | tuple[torch.Tensor, ...]:
        r"""

        Example:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoProcessor, MllamaVisionModel

        >>> checkpoint = "meta-llama/Llama-3.2-11B-Vision"
        >>> model = MllamaVisionModel.from_pretrained(checkpoint)
        >>> processor = AutoProcessor.from_pretrained(checkpoint)

        >>> url = "https://www.ilankelman.org/stopsigns/australia.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = processor(images=image, return_tensors="pt")

        >>> output = model(**inputs)

        >>> print(output.last_hidden_state.shape)
        torch.Size([1, 1, 4, 1025, 7680])
        ```
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # num_concurrent_media and num_chunks are both currently 1
        batch_size_times_num_tiles, num_channels, height, width = pixel_values.shape
        num_concurrent_media = 1
        num_chunks = 1
        hidden_state = self.patch_embedding(pixel_values)
        _, num_patches, hidden_dim = hidden_state.shape

        # Add cls token
        hidden_state = hidden_state.reshape(
            batch_size_times_num_tiles * num_concurrent_media * num_chunks, num_patches, hidden_dim
        )
        class_embedding = self.class_embedding.expand(hidden_state.shape[0], 1, hidden_state.shape[-1])
        hidden_state = torch.cat([hidden_state, class_embedding], dim=1)
        num_patches += 1

        # Position embeddings
        hidden_state = hidden_state.reshape(
            batch_size_times_num_tiles * num_concurrent_media, num_chunks, num_patches, hidden_dim
        )
        positional_embedding = self.positional_embedding_vlm.to(dtype=hidden_state.dtype, device=hidden_state.device)
        hidden_state = hidden_state + positional_embedding

        hidden_state = self.layernorm_pre(hidden_state)

        hidden_state = hidden_state.view(batch_size_times_num_tiles, -1, hidden_dim)
        freqs_ci = self.rotary_embedding(pixel_values)

        output = self.model(
            hidden_state,
            attention_mask=None,
            output_hidden_states=output_hidden_states,
            output_attentions=output_attentions,
            freqs_ci=freqs_ci,
        )

        hidden_state = output.last_hidden_state

        hidden_state = self.layernorm_post(hidden_state)

        hidden_state = hidden_state[:, :-1, :]

        # now, we use Llama4VisionPixelShuffle + mlp to project embeddings
        hidden_state = self.vision_adapter(hidden_state)

        hidden_states = output.hidden_states if output_hidden_states else None

        if output_attentions:
            attentions = output[2]
        else:
            attentions = None

        if not return_dict:
            return tuple(v for v in [hidden_state, hidden_states, attentions] if v is not None)

        return BaseModelOutputWithPooling(
            last_hidden_state=hidden_state,
            hidden_states=hidden_states,
            attentions=attentions,
        )