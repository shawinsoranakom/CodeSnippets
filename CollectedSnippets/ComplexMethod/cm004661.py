def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        visual_embeds: torch.FloatTensor | None = None,
        visual_attention_mask: torch.LongTensor | None = None,
        visual_token_type_ids: torch.LongTensor | None = None,
        image_text_alignment: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        labels: torch.LongTensor | None = None,
        sentence_image_labels: torch.LongTensor | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | VisualBertForPreTrainingOutput:
        r"""
        visual_embeds (`torch.FloatTensor` of shape `(batch_size, visual_seq_length, visual_embedding_dim)`, *optional*):
            The embedded representation of the visual inputs, generally derived using using an object detector.
        visual_attention_mask (`torch.FloatTensor` of shape `(batch_size, visual_seq_length)`, *optional*):
            Mask to avoid performing attention on visual embeddings. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)
        visual_token_type_ids (`torch.LongTensor` of shape `(batch_size, visual_seq_length)`, *optional*):
            Segment token indices to indicate different portions of the visual embeds.

            [What are token type IDs?](../glossary#token-type-ids) The authors of VisualBERT set the
            *visual_token_type_ids* to *1* for all tokens.
        image_text_alignment (`torch.LongTensor` of shape `(batch_size, visual_seq_length, alignment_number)`, *optional*):
            Image-Text alignment uses to decide the position IDs of the visual embeddings.
        labels (`torch.LongTensor` of shape `(batch_size, total_sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should be in `[-100, 0, ...,
            config.vocab_size]` (see `input_ids` docstring) Tokens with indices set to `-100` are ignored (masked), the
            loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`
        sentence_image_labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sentence-image prediction (classification) loss. Input should be a sequence pair
            (see `input_ids` docstring) Indices should be in `[0, 1]`:

            - 0 indicates sequence B is a matching pair of sequence A for the given image,
            - 1 indicates sequence B is a random sequence w.r.t A for the given image.

        Example:

        ```python
        # Assumption: *get_visual_embeddings(image)* gets the visual embeddings of the image in the batch.
        from transformers import AutoTokenizer, VisualBertForPreTraining

        tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")
        model = VisualBertForPreTraining.from_pretrained("uclanlp/visualbert-vqa-coco-pre")

        inputs = tokenizer("The capital of France is [MASK].", return_tensors="pt")
        visual_embeds = get_visual_embeddings(image).unsqueeze(0)
        visual_token_type_ids = torch.ones(visual_embeds.shape[:-1], dtype=torch.long)
        visual_attention_mask = torch.ones(visual_embeds.shape[:-1], dtype=torch.float)

        inputs.update(
            {
                "visual_embeds": visual_embeds,
                "visual_token_type_ids": visual_token_type_ids,
                "visual_attention_mask": visual_attention_mask,
            }
        )
        max_length = inputs["input_ids"].shape[-1] + visual_embeds.shape[-2]
        labels = tokenizer(
            "The capital of France is Paris.", return_tensors="pt", padding="max_length", max_length=max_length
        )["input_ids"]
        sentence_image_labels = torch.tensor(1).unsqueeze(0)  # Batch_size


        outputs = model(**inputs, labels=labels, sentence_image_labels=sentence_image_labels)
        loss = outputs.loss
        prediction_logits = outputs.prediction_logits
        seq_relationship_logits = outputs.seq_relationship_logits
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if labels is not None:
            total_size = attention_mask.size(-1) + visual_attention_mask.size(-1)
            if labels.size(-1) != total_size:
                raise ValueError(
                    "The labels provided should have same sequence length as total attention mask. "
                    f"Found labels with sequence length {labels.size(-1)}, expected {total_size}."
                )

        outputs = self.visual_bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            visual_embeds=visual_embeds,
            visual_attention_mask=visual_attention_mask,
            visual_token_type_ids=visual_token_type_ids,
            image_text_alignment=image_text_alignment,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output, pooled_output = outputs[:2]
        prediction_scores, seq_relationship_score = self.cls(sequence_output, pooled_output)

        total_loss = None
        if labels is not None and sentence_image_labels is not None:
            loss_fct = CrossEntropyLoss()
            masked_lm_loss = loss_fct(prediction_scores.view(-1, self.config.vocab_size), labels.view(-1))
            sentence_image_loss = loss_fct(seq_relationship_score.view(-1, 2), sentence_image_labels.view(-1))
            total_loss = masked_lm_loss + sentence_image_loss

        elif labels is not None:
            loss_fct = CrossEntropyLoss()
            total_loss = loss_fct(prediction_scores.view(-1, self.config.vocab_size), labels.view(-1))

        if not return_dict:
            output = (prediction_scores, seq_relationship_score) + outputs[2:]
            return ((total_loss,) + output) if total_loss is not None else output

        return VisualBertForPreTrainingOutput(
            loss=total_loss,
            prediction_logits=prediction_scores,
            seq_relationship_logits=seq_relationship_score,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )