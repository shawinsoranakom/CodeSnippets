def forward(
        self,
        pixel_values: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> SemanticSegmenterOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size, height, width)`, *optional*):
            Ground truth semantic segmentation maps for computing the loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels > 1`, a classification loss is computed (Cross-Entropy).

        Examples:
        ```python
        >>> from transformers import AutoImageProcessor, DPTForSemanticSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("Intel/dpt-large-ade")
        >>> model = DPTForSemanticSegmentation.from_pretrained("Intel/dpt-large-ade")

        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> logits = outputs.logits
        ```"""
        if labels is not None and self.config.num_labels == 1:
            raise ValueError("The number of labels should be greater than one")

        # Internally the model always needs to output hidden states, we control the output
        # per user request on the final output
        user_requested_hidden_states = kwargs.get("output_hidden_states") or getattr(
            self.config, "output_hidden_states", False
        )
        kwargs["output_hidden_states"] = True

        outputs: BaseModelOutputWithPoolingAndIntermediateActivations = self.dpt(pixel_values, **kwargs)
        hidden_states = outputs.hidden_states

        # only keep certain features based on config.backbone_out_indices
        # note that the hidden_states also include the initial embeddings
        if not self.config.is_hybrid:
            hidden_states = [
                feature for idx, feature in enumerate(hidden_states[1:]) if idx in self.config.backbone_out_indices
            ]
        else:
            backbone_hidden_states = outputs.intermediate_activations
            backbone_hidden_states.extend(
                feature for idx, feature in enumerate(hidden_states[1:]) if idx in self.config.backbone_out_indices[2:]
            )

            hidden_states = backbone_hidden_states

        hidden_states = self.neck(hidden_states=hidden_states)
        logits = self.head(hidden_states)

        auxiliary_logits = None
        if self.auxiliary_head is not None:
            auxiliary_logits = self.auxiliary_head(hidden_states[-1])

        loss = None
        if labels is not None:
            # upsample logits to the images' original size
            upsampled_logits = nn.functional.interpolate(
                logits, size=labels.shape[-2:], mode="bilinear", align_corners=False
            )
            if auxiliary_logits is not None:
                upsampled_auxiliary_logits = nn.functional.interpolate(
                    auxiliary_logits, size=labels.shape[-2:], mode="bilinear", align_corners=False
                )
            # compute weighted loss
            loss_fct = CrossEntropyLoss(ignore_index=self.config.semantic_loss_ignore_index)
            main_loss = loss_fct(upsampled_logits, labels)
            auxiliary_loss = loss_fct(upsampled_auxiliary_logits, labels)
            loss = main_loss + self.config.auxiliary_loss_weight * auxiliary_loss

        return SemanticSegmenterOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states if user_requested_hidden_states else None,
            attentions=outputs.attentions,
        )