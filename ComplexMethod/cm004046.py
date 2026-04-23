def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        pixel_mask: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        image_embeds: torch.FloatTensor | None = None,
        image_token_type_idx: int | None = None,
        labels: torch.LongTensor | None = None,
        interpolate_pos_encoding: bool = False,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | BridgeTowerModelOutput:
        r"""
        image_embeds (`torch.FloatTensor` of shape `(batch_size, num_patches, hidden_size)`, *optional*):
            Optionally, instead of passing `pixel_values`, you can choose to directly pass an embedded representation.
            This is useful if you want more control over how to convert `pixel_values` into patch embeddings.
        image_token_type_idx (`int`, *optional*):
            - The token type ids for images.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels are currently not supported.

        Examples:

        ```python
        >>> from transformers import BridgeTowerProcessor, BridgeTowerModel
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> # prepare image and text
        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> text = "hello world"
        >>> processor = BridgeTowerProcessor.from_pretrained("BridgeTower/bridgetower-base")
        >>> model = BridgeTowerModel.from_pretrained("BridgeTower/bridgetower-base")

        >>> inputs = processor(image, text, return_tensors="pt")
        >>> outputs = model(**inputs)
        >>> outputs.keys()
        odict_keys(['text_features', 'image_features', 'pooler_output'])
        ```"""
        all_hidden_states_text = []
        all_hidden_states_image = []
        all_hidden_states_cross = []
        all_self_attentions = []

        if inputs_embeds is not None and input_ids is None:
            raise NotImplementedError(
                "BridgeTowerModel does not use `inputs_embeds`.  Make sure to pass in `input_ids` instead."
            )

        image_token_type_idx = image_token_type_idx or 1
        input_shape = input_ids.size()
        text_embeds = self.text_model.embeddings(input_ids=input_ids)
        all_hidden_states_text.append(text_embeds)

        if attention_mask is None:
            attention_mask = torch.ones(input_shape, dtype=torch.long, device=input_ids.device)
        extend_text_masks = self.text_model.get_extended_attention_mask(attention_mask, input_shape).to(
            input_ids.device
        )

        # The split_index determines how many layers of the uni-modal encoder are applied before the cross-modal encoder
        split_index = len(self.text_model.encoder.layer) - self.config.num_hidden_layers + 1

        # Run the first 'split_index' layers of the textual encoder
        for layer in self.text_model.encoder.layer[:split_index]:
            text_embeds = layer(text_embeds, extend_text_masks)
            all_hidden_states_text.append(text_embeds)

        if image_embeds is None:
            image_embeds = self.vision_model.visual.forward_pre(
                pixel_values.type(self.vision_model.dtype), interpolate_pos_encoding=interpolate_pos_encoding
            )
        else:
            # Permute as BridgeTowerResidualAttention has batch_first=True
            image_embeds = image_embeds.permute(1, 0, 2)

        all_hidden_states_image.append(image_embeds)

        # Run the first 'split_index' layers of the visual encoder
        for block in self.vision_model.visual.transformer.resblocks[:split_index]:
            image_embeds = block(image_embeds)
            all_hidden_states_image.append(image_embeds)

        image_embeds_with_ln = self.vision_model.visual.forward_post(image_embeds.type(self.vision_model.dtype))

        # first layer is a special case because we don't have the output from the cross-encoder yet
        cross_modal_text = self._apply_text_transform(text_embeds, layer_idx=0)

        text_token_type_embeddings = self.token_type_embeddings(
            torch.zeros(1, dtype=torch.long, device=input_ids.device)
        ).expand_as(cross_modal_text)

        cross_modal_text = self.cross_modal_text_layernorm(cross_modal_text + text_token_type_embeddings)

        image_embeds_with_ln = self._apply_image_transform(image_embeds_with_ln, layer_idx=0)
        image_token_type_embeddings = self.token_type_embeddings(
            torch.full((1,), image_token_type_idx, dtype=torch.long, device=input_ids.device)
        ).expand_as(image_embeds_with_ln)

        image_embeds_with_ln = image_embeds_with_ln + image_token_type_embeddings
        cross_modal_image = self.cross_modal_image_layernorm(image_embeds_with_ln)

        pixel_mask = torch.ones(
            (cross_modal_image.size(0), cross_modal_image.size(1)),
            dtype=torch.long,
            device=input_ids.device,
        )
        extend_image_masks = self.text_model.get_extended_attention_mask(pixel_mask, pixel_mask.size()).to(
            input_ids.device
        )

        layer_outputs_text = self.cross_modal_text_layers[0](
            cross_modal_text,
            cross_modal_image,
            attention_mask=extend_text_masks,
            encoder_attention_mask=extend_image_masks,
        )
        cross_text_features = layer_outputs_text[0]

        layer_outputs_image = self.cross_modal_image_layers[0](
            cross_modal_image,
            cross_modal_text,
            attention_mask=extend_image_masks,
            encoder_attention_mask=extend_text_masks,
        )
        cross_image_features = layer_outputs_image[0]

        all_hidden_states_cross.append((cross_text_features, cross_image_features))

        all_self_attentions.append((layer_outputs_text[1], layer_outputs_image[1]))

        link_layer_index = 0

        #  Each of the top 6 layers of the visual and textual encoders ([split_index:]) is connected to each layer of
        #  the cross-modal encoder via bridge layers, which brings bottom-up alignment and fusion to the cross-modal encoder.
        for i in range(split_index, len(self.text_model.encoder.layer)):
            text_embeds = self.text_model.encoder.layer[i](text_embeds, extend_text_masks)
            image_embeds = self.vision_model.visual.transformer.resblocks[i](image_embeds).type(
                self.vision_model.dtype
            )
            image_embeds_with_ln = (
                self._apply_image_transform(self.vision_model.visual.forward_post(image_embeds), link_layer_index + 1)
                + image_token_type_embeddings
            )

            text_link_tower = self.cross_modal_text_link_tower[link_layer_index]
            image_link_tower = self.cross_modal_image_link_tower[link_layer_index]

            # Bridge layers for textual and visual encoders
            transformed_text_embeds = self._apply_text_transform(text_embeds, link_layer_index + 1)
            cross_text_features_ = text_link_tower(
                transformed_text_embeds + text_token_type_embeddings,
                cross_text_features,
                extend_text_masks,
            )
            cross_image_features_ = image_link_tower(image_embeds_with_ln, cross_image_features, extend_image_masks)

            # Cross-modal encoder via bridge layers of textual and visual encoders
            layer_outputs_text = self.cross_modal_text_layers[link_layer_index + 1](
                cross_text_features_,
                cross_image_features_,
                attention_mask=extend_text_masks,
                encoder_attention_mask=extend_image_masks,
            )
            cross_text_features = layer_outputs_text[0]

            layer_outputs_image = self.cross_modal_image_layers[link_layer_index + 1](
                cross_image_features_,
                cross_text_features_,
                attention_mask=extend_image_masks,
                encoder_attention_mask=extend_text_masks,
            )
            cross_image_features = layer_outputs_image[0]

            link_layer_index += 1

            all_hidden_states_text.append(text_embeds)
            all_hidden_states_image.append(image_embeds)
            all_hidden_states_cross.append((cross_text_features, cross_image_features))

            all_self_attentions.append((layer_outputs_text[1], layer_outputs_image[1]))

        #  Concatenate the cls token of the text and image features to get the final represtation
        text_features, image_features = cross_text_features, cross_image_features
        cls_features = self.get_cls_features(text_features, image_features)

        return BridgeTowerModelOutput(
            text_features=text_features,
            image_features=image_features,
            pooler_output=cls_features,
            hidden_states=(
                tuple(all_hidden_states_text),
                tuple(all_hidden_states_image),
                tuple(all_hidden_states_cross),
            ),
            attentions=tuple(all_self_attentions),
        )