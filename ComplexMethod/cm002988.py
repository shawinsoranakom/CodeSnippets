def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        bbox: torch.LongTensor | None = None,
        image: torch.FloatTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | SequenceClassifierOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `batch_size, sequence_length`):
            Indices of input sequence tokens in the vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        bbox (`torch.LongTensor` of shape `(batch_size, sequence_length, 4)`, *optional*):
            Bounding boxes of each input sequence tokens. Selected in the range `[0,
            config.max_2d_position_embeddings-1]`. Each bounding box should be a normalized version in (x0, y0, x1, y1)
            format, where (x0, y0) corresponds to the position of the upper left corner in the bounding box, and (x1,
            y1) represents the position of the lower right corner.
        image (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)` or `detectron.structures.ImageList` whose `tensors` is of shape `(batch_size, num_channels, height, width)`):
            Batch of document images.
        token_type_ids (`torch.LongTensor` of shape `batch_size, sequence_length`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`:

            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.

            [What are token type IDs?](../glossary#token-type-ids)
        position_ids (`torch.LongTensor` of shape `batch_size, sequence_length`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).

        Example:

        ```python
        >>> from transformers import AutoProcessor, LayoutLMv2ForSequenceClassification, set_seed
        >>> from PIL import Image
        >>> import torch
        >>> from datasets import load_dataset

        >>> set_seed(0)

        >>> dataset = load_dataset("aharley/rvl_cdip", split="train", streaming=True)
        >>> data = next(iter(dataset))
        >>> image = data["image"].convert("RGB")

        >>> processor = AutoProcessor.from_pretrained("microsoft/layoutlmv2-base-uncased")
        >>> model = LayoutLMv2ForSequenceClassification.from_pretrained(
        ...     "microsoft/layoutlmv2-base-uncased", num_labels=dataset.info.features["label"].num_classes
        ... )

        >>> encoding = processor(image, return_tensors="pt")
        >>> sequence_label = torch.tensor([data["label"]])

        >>> outputs = model(**encoding, labels=sequence_label)

        >>> loss, logits = outputs.loss, outputs.logits
        >>> predicted_idx = logits.argmax(dim=-1).item()
        >>> predicted_answer = dataset.info.features["label"].names[4]
        >>> predicted_idx, predicted_answer  # results are not good without further fine-tuning
        (7, 'advertisement')
        ```
        """

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            self.warn_if_padding_and_no_attention_mask(input_ids, attention_mask)
            input_shape = input_ids.size()
        elif inputs_embeds is not None:
            input_shape = inputs_embeds.size()[:-1]
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        visual_shape = list(input_shape)
        visual_shape[1] = self.config.image_feature_pool_shape[0] * self.config.image_feature_pool_shape[1]
        visual_shape = torch.Size(visual_shape)
        final_shape = list(input_shape)
        final_shape[1] += visual_shape[1]
        final_shape = torch.Size(final_shape)

        visual_bbox = self.layoutlmv2._calc_visual_bbox(
            self.config.image_feature_pool_shape, bbox, device, final_shape
        )

        visual_position_ids = torch.arange(0, visual_shape[1], dtype=torch.long, device=device).repeat(
            input_shape[0], 1
        )

        initial_image_embeddings = self.layoutlmv2._calc_img_embeddings(
            image=image,
            bbox=visual_bbox,
            position_ids=visual_position_ids,
        )

        outputs: BaseModelOutputWithPooling = self.layoutlmv2(
            input_ids=input_ids,
            bbox=bbox,
            image=image,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )
        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        seq_length = input_shape[1]
        sequence_output, final_image_embeddings = (
            outputs.last_hidden_state[:, :seq_length],
            outputs.last_hidden_state[:, seq_length:],
        )

        cls_final_output = sequence_output[:, 0, :]

        # average-pool the visual embeddings
        pooled_initial_image_embeddings = initial_image_embeddings.mean(dim=1)
        pooled_final_image_embeddings = final_image_embeddings.mean(dim=1)
        # concatenate with cls_final_output
        sequence_output = torch.cat(
            [cls_final_output, pooled_initial_image_embeddings, pooled_final_image_embeddings], dim=1
        )
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)

        loss = None
        if labels is not None:
            if self.config.problem_type is None:
                if self.num_labels == 1:
                    self.config.problem_type = "regression"
                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
                    self.config.problem_type = "single_label_classification"
                else:
                    self.config.problem_type = "multi_label_classification"

            if self.config.problem_type == "regression":
                loss_fct = MSELoss()
                if self.num_labels == 1:
                    loss = loss_fct(logits.squeeze(), labels.squeeze())
                else:
                    loss = loss_fct(logits, labels)
            elif self.config.problem_type == "single_label_classification":
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            elif self.config.problem_type == "multi_label_classification":
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(logits, labels)

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )