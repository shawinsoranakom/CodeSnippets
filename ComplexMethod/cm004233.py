def forward(
        self,
        pixel_values: torch.FloatTensor | None = None,
        pixel_mask: torch.LongTensor | None = None,
        decoder_attention_mask: torch.FloatTensor | None = None,
        encoder_outputs: torch.FloatTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.FloatTensor] | DetrModelOutput:
        r"""
        decoder_attention_mask (`torch.FloatTensor` of shape `(batch_size, num_queries)`, *optional*):
            Mask to avoid performing attention on certain object queries in the decoder. Mask values selected in `[0, 1]`:

            - 1 for queries that are **not masked**,
            - 0 for queries that are **masked**.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing the flattened feature map (output of the backbone + projection layer), you
            can choose to directly pass a flattened representation of an image. Useful for bypassing the vision backbone.
        decoder_inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_size)`, *optional*):
            Optionally, instead of initializing the queries with a tensor of zeros, you can choose to directly pass an
            embedded representation. Useful for tasks that require custom query initialization.

        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, DetrModel
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/detr-resnet-50")
        >>> model = DetrModel.from_pretrained("facebook/detr-resnet-50")

        >>> # prepare image for the model
        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> # forward pass
        >>> outputs = model(**inputs)

        >>> # the last hidden states are the final query embeddings of the Transformer decoder
        >>> # these are of shape (batch_size, num_queries, hidden_size)
        >>> last_hidden_states = outputs.last_hidden_state
        >>> list(last_hidden_states.shape)
        [1, 100, 256]
        ```"""
        if pixel_values is None and inputs_embeds is None:
            raise ValueError("You have to specify either pixel_values or inputs_embeds")

        if inputs_embeds is None:
            batch_size, num_channels, height, width = pixel_values.shape
            device = pixel_values.device

            if pixel_mask is None:
                pixel_mask = torch.ones(((batch_size, height, width)), device=device)
            vision_features = self.backbone(pixel_values, pixel_mask)
            feature_map, mask = vision_features[-1]

            # Apply 1x1 conv to map (batch_size, C, H, W) -> (batch_size, hidden_size, H, W), then flatten to (batch_size, HW, hidden_size)
            # Position embeddings are already flattened to (batch_size, sequence_length, hidden_size) format
            projected_feature_map = self.input_projection(feature_map)
            flattened_features = projected_feature_map.flatten(2).permute(0, 2, 1)
            spatial_position_embeddings = self.position_embedding(
                shape=feature_map.shape, device=device, dtype=pixel_values.dtype, mask=mask
            )
            flattened_mask = mask.flatten(1)
        else:
            batch_size = inputs_embeds.shape[0]
            device = inputs_embeds.device
            flattened_features = inputs_embeds
            # When using inputs_embeds, we need to infer spatial dimensions for position embeddings
            # Assume square feature map
            seq_len = inputs_embeds.shape[1]
            feat_dim = int(seq_len**0.5)
            # Create position embeddings for the inferred spatial size
            spatial_position_embeddings = self.position_embedding(
                shape=torch.Size([batch_size, self.config.d_model, feat_dim, feat_dim]),
                device=device,
                dtype=inputs_embeds.dtype,
            )
            # If a pixel_mask is provided with inputs_embeds, interpolate it to feat_dim, then flatten.
            if pixel_mask is not None:
                mask = nn.functional.interpolate(pixel_mask[None].float(), size=(feat_dim, feat_dim)).to(torch.bool)[0]
                flattened_mask = mask.flatten(1)
            else:
                # If no mask provided, assume all positions are valid
                flattened_mask = torch.ones((batch_size, seq_len), device=device, dtype=torch.long)

        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                inputs_embeds=flattened_features,
                attention_mask=flattened_mask,
                spatial_position_embeddings=spatial_position_embeddings,
                **kwargs,
            )

        object_queries_position_embeddings = self.query_position_embeddings.weight.unsqueeze(0).repeat(
            batch_size, 1, 1
        )

        # Use decoder_inputs_embeds as queries if provided, otherwise initialize with zeros
        if decoder_inputs_embeds is not None:
            queries = decoder_inputs_embeds
        else:
            queries = torch.zeros_like(object_queries_position_embeddings)

        # decoder outputs consists of (dec_features, dec_hidden, dec_attn)
        decoder_outputs = self.decoder(
            inputs_embeds=queries,
            attention_mask=decoder_attention_mask,
            spatial_position_embeddings=spatial_position_embeddings,
            object_queries_position_embeddings=object_queries_position_embeddings,
            encoder_hidden_states=encoder_outputs.last_hidden_state,
            encoder_attention_mask=flattened_mask,
            **kwargs,
        )

        return DetrModelOutput(
            last_hidden_state=decoder_outputs.last_hidden_state,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
            intermediate_hidden_states=decoder_outputs.intermediate_hidden_states,
        )