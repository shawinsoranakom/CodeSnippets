def forward(
        self,
        inputs: torch.FloatTensor,
        attention_mask: torch.FloatTensor | None = None,
        subsampled_output_points: dict[str, torch.Tensor] | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        interpolate_pos_encoding: bool = False,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | PerceiverModelOutput:
        r"""
        inputs (`torch.FloatTensor`):
            Inputs to the perceiver. Can be anything: images, text, audio, video, etc.
        subsampled_output_points (`dict[str, torch.Tensor]`, *optional*):
            Dictionary of tensors used as queries for the decoder. The decoder maps these queries to the latent
            representation of the model. Used for subsampled decoding, e.g. when only decoding certain image patches.

        Examples:

        ```python
        >>> from transformers import PerceiverConfig, PerceiverTokenizer, PerceiverImageProcessor, PerceiverModel
        >>> from transformers.models.perceiver.modeling_perceiver import (
        ...     PerceiverTextPreprocessor,
        ...     PerceiverImagePreprocessor,
        ...     PerceiverClassificationDecoder,
        ... )
        >>> import torch
        >>> import httpx
        >>> from io import BytesIO
        >>> from PIL import Image

        >>> # EXAMPLE 1: using the Perceiver to classify texts
        >>> # - we define a TextPreprocessor, which can be used to embed tokens
        >>> # - we define a ClassificationDecoder, which can be used to decode the
        >>> # final hidden states of the latents to classification logits
        >>> # using trainable position embeddings
        >>> config = PerceiverConfig()
        >>> preprocessor = PerceiverTextPreprocessor(config)
        >>> decoder = PerceiverClassificationDecoder(
        ...     config,
        ...     num_channels=config.d_latents,
        ...     trainable_position_encoding_kwargs=dict(num_channels=config.d_latents, index_dims=1),
        ...     use_query_residual=True,
        ... )
        >>> model = PerceiverModel(config, input_preprocessor=preprocessor, decoder=decoder)

        >>> # you can then do a forward pass as follows:
        >>> tokenizer = PerceiverTokenizer()
        >>> text = "hello world"
        >>> inputs = tokenizer(text, return_tensors="pt").input_ids

        >>> with torch.no_grad():
        ...     outputs = model(inputs=inputs)
        >>> logits = outputs.logits
        >>> list(logits.shape)
        [1, 2]

        >>> # to train, one can train the model using standard cross-entropy:
        >>> criterion = torch.nn.CrossEntropyLoss()

        >>> labels = torch.tensor([1])
        >>> loss = criterion(logits, labels)

        >>> # EXAMPLE 2: using the Perceiver to classify images
        >>> # - we define an ImagePreprocessor, which can be used to embed images
        >>> config = PerceiverConfig(image_size=224)
        >>> preprocessor = PerceiverImagePreprocessor(
        ...     config,
        ...     prep_type="conv1x1",
        ...     spatial_downsample=1,
        ...     out_channels=256,
        ...     position_encoding_type="trainable",
        ...     concat_or_add_pos="concat",
        ...     project_pos_dim=256,
        ...     trainable_position_encoding_kwargs=dict(
        ...         num_channels=256,
        ...         index_dims=config.image_size**2,
        ...     ),
        ... )

        >>> model = PerceiverModel(
        ...     config,
        ...     input_preprocessor=preprocessor,
        ...     decoder=PerceiverClassificationDecoder(
        ...         config,
        ...         num_channels=config.d_latents,
        ...         trainable_position_encoding_kwargs=dict(num_channels=config.d_latents, index_dims=1),
        ...         use_query_residual=True,
        ...     ),
        ... )

        >>> # you can then do a forward pass as follows:
        >>> image_processor = PerceiverImageProcessor()
        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = image_processor(image, return_tensors="pt").pixel_values

        >>> with torch.no_grad():
        ...     outputs = model(inputs=inputs)
        >>> logits = outputs.logits
        >>> list(logits.shape)
        [1, 2]

        >>> # to train, one can train the model using standard cross-entropy:
        >>> criterion = torch.nn.CrossEntropyLoss()

        >>> labels = torch.tensor([1])
        >>> loss = criterion(logits, labels)
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if self.input_preprocessor is not None:
            inputs, modality_sizes, inputs_without_pos = self.input_preprocessor(
                inputs, interpolate_pos_encoding=interpolate_pos_encoding
            )
        else:
            modality_sizes = None
            inputs_without_pos = None
            if inputs.size()[-1] != self.config.d_model:
                raise ValueError(
                    f"Last dimension of the inputs: {inputs.size()[-1]} doesn't correspond to config.d_model:"
                    f" {self.config.d_model}. Make sure to set config.d_model appropriately."
                )

        batch_size, seq_length, _ = inputs.size()
        device = inputs.device

        # If no attention mask is provided, make them all ones
        if attention_mask is None:
            attention_mask = torch.ones((batch_size, seq_length), device=device)
        # Make the attention mask broadcastable to [batch_size, num_heads, seq_length, seq_length]
        extended_attention_mask = self.invert_attention_mask(attention_mask)

        embedding_output = self.embeddings(batch_size=batch_size)

        encoder_outputs = self.encoder(
            embedding_output,
            attention_mask=None,
            inputs=inputs,
            inputs_mask=extended_attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        sequence_output = encoder_outputs[0]

        logits = None
        if self.decoder:
            if subsampled_output_points is not None:
                output_modality_sizes = {
                    "audio": subsampled_output_points["audio"].shape[0],
                    "image": subsampled_output_points["image"].shape[0],
                    "label": 1,
                }
            else:
                output_modality_sizes = modality_sizes
            decoder_query = self.decoder.decoder_query(
                inputs, modality_sizes, inputs_without_pos, subsampled_points=subsampled_output_points
            )
            decoder_outputs = self.decoder(
                decoder_query,
                z=sequence_output,
                query_mask=extended_attention_mask,
                output_attentions=output_attentions,
            )
            logits = decoder_outputs.logits

            # add cross-attentions of decoder
            if output_attentions and decoder_outputs.cross_attentions is not None:
                if return_dict:
                    encoder_outputs.cross_attentions = (
                        encoder_outputs.cross_attentions + decoder_outputs.cross_attentions
                    )
                else:
                    encoder_outputs = encoder_outputs + decoder_outputs.cross_attentions

            if self.output_postprocessor:
                logits = self.output_postprocessor(logits, modality_sizes=output_modality_sizes)

        if not return_dict:
            if logits is not None:
                return (logits, sequence_output) + encoder_outputs[1:]
            else:
                return (sequence_output,) + encoder_outputs[1:]

        return PerceiverModelOutput(
            logits=logits,
            last_hidden_state=sequence_output,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
            cross_attentions=encoder_outputs.cross_attentions,
        )