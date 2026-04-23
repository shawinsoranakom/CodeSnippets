def forward(
        self,
        pixel_values: torch.FloatTensor,
        pixel_mask: torch.LongTensor | None = None,
        decoder_attention_mask: torch.LongTensor | None = None,
        encoder_outputs: torch.FloatTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.FloatTensor] | DabDetrModelOutput:
        r"""
        decoder_attention_mask (`torch.FloatTensor` of shape `(batch_size, num_queries)`, *optional*):
            Not used by default. Can be used to mask object queries.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing the flattened feature map (output of the backbone + projection layer), you
            can choose to directly pass a flattened representation of an image.
        decoder_inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_size)`, *optional*):
            Optionally, instead of initializing the queries with a tensor of zeros, you can choose to directly pass an
            embedded representation.

        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, AutoModel
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("IDEA-Research/dab-detr-resnet-50")
        >>> model = AutoModel.from_pretrained("IDEA-Research/dab-detr-resnet-50")

        >>> # prepare image for the model
        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> # forward pass
        >>> outputs = model(**inputs)

        >>> # the last hidden states are the final query embeddings of the Transformer decoder
        >>> # these are of shape (batch_size, num_queries, hidden_size)
        >>> last_hidden_states = outputs.last_hidden_state
        >>> list(last_hidden_states.shape)
        [1, 300, 256]
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        batch_size, _, height, width = pixel_values.shape
        device = pixel_values.device

        if pixel_mask is None:
            pixel_mask = torch.ones(((batch_size, height, width)), device=device)

        # First, sent pixel_values + pixel_mask through Backbone to obtain the features
        # pixel_values should be of shape (batch_size, num_channels, height, width)
        # pixel_mask should be of shape (batch_size, height, width)
        features, object_queries_list = self.backbone(pixel_values, pixel_mask)

        # get final feature map and downsampled mask
        feature_map, mask = features[-1]

        if mask is None:
            raise ValueError("Backbone does not return downsampled pixel mask")

        flattened_mask = mask.flatten(1)

        # Second, apply 1x1 convolution to reduce the channel dimension to hidden_size (256 by default)
        projected_feature_map = self.input_projection(feature_map)

        # Third, flatten the feature map + object_queries of shape NxCxHxW to HWxNxC, and permute it to NxHWxC
        # In other words, turn their shape into ( sequence_length, batch_size, hidden_size)
        flattened_features = projected_feature_map.flatten(2).permute(0, 2, 1)
        object_queries = object_queries_list[-1].flatten(2).permute(0, 2, 1)
        reference_position_embeddings = self.query_refpoint_embeddings.weight.unsqueeze(0).repeat(batch_size, 1, 1)

        # Fourth, sent flattened_features + flattened_mask + object_queries through encoder
        # flattened_features is a Tensor of shape (height*width, batch_size, hidden_size)
        # flattened_mask is a Tensor of shape (batch_size, height*width)
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                inputs_embeds=flattened_features,
                attention_mask=flattened_mask,
                object_queries=object_queries,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )
        # If the user passed a tuple for encoder_outputs, we wrap it in a BaseModelOutput when return_dict=True
        elif return_dict and not isinstance(encoder_outputs, BaseModelOutput):
            encoder_outputs = BaseModelOutput(
                last_hidden_state=encoder_outputs[0],
                hidden_states=encoder_outputs[1] if len(encoder_outputs) > 1 else None,
                attentions=encoder_outputs[2] if len(encoder_outputs) > 2 else None,
            )

        # Fifth, sent query embeddings + object_queries through the decoder (which is conditioned on the encoder output)
        num_queries = reference_position_embeddings.shape[1]
        if self.num_patterns == 0:
            queries = torch.zeros(batch_size, num_queries, self.hidden_size, device=device)
        else:
            queries = (
                self.patterns.weight[:, None, None, :]
                .repeat(1, self.num_queries, batch_size, 1)
                .flatten(0, 1)
                .permute(1, 0, 2)
            )  # bs, n_q*n_pat, hidden_size
            reference_position_embeddings = reference_position_embeddings.repeat(
                1, self.num_patterns, 1
            )  # bs, n_q*n_pat,  hidden_size

        # decoder outputs consists of (dec_features, dec_hidden, dec_attn)
        decoder_outputs = self.decoder(
            inputs_embeds=queries,
            query_position_embeddings=reference_position_embeddings,
            object_queries=object_queries,
            encoder_hidden_states=encoder_outputs[0],
            memory_key_padding_mask=flattened_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        if not return_dict:
            # last_hidden_state
            output = (decoder_outputs[0],)
            reference_points = decoder_outputs[-1]
            intermediate_hidden_states = decoder_outputs[-2]

            # it has to follow the order of DABDETRModelOutput that is based on ModelOutput
            # If we only use one of the variables then the indexing will change.
            # E.g: if we return everything then 'decoder_attentions' is decoder_outputs[2], if we only use output_attentions then its decoder_outputs[1]
            if output_hidden_states and output_attentions:
                output += (
                    decoder_outputs[1],
                    decoder_outputs[2],
                    decoder_outputs[3],
                    encoder_outputs[0],
                    encoder_outputs[1],
                    encoder_outputs[2],
                )
            elif output_hidden_states:
                # decoder_hidden_states, encoder_last_hidden_state, encoder_hidden_states
                output += (
                    decoder_outputs[1],
                    encoder_outputs[0],
                    encoder_outputs[1],
                )
            elif output_attentions:
                # decoder_self_attention, decoder_cross_attention, encoder_attentions
                output += (
                    decoder_outputs[1],
                    decoder_outputs[2],
                    encoder_outputs[1],
                )

            output += (intermediate_hidden_states, reference_points)

            return output

        reference_points = decoder_outputs.reference_points
        intermediate_hidden_states = decoder_outputs.intermediate_hidden_states

        return DabDetrModelOutput(
            last_hidden_state=decoder_outputs.last_hidden_state,
            decoder_hidden_states=decoder_outputs.hidden_states if output_hidden_states else None,
            decoder_attentions=decoder_outputs.attentions if output_attentions else None,
            cross_attentions=decoder_outputs.cross_attentions if output_attentions else None,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state if output_hidden_states else None,
            encoder_hidden_states=encoder_outputs.hidden_states if output_hidden_states else None,
            encoder_attentions=encoder_outputs.attentions if output_attentions else None,
            intermediate_hidden_states=intermediate_hidden_states,
            reference_points=reference_points,
        )