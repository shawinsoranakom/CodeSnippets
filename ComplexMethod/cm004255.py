def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        pixel_mask: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        image_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> ViltForImagesAndTextClassificationOutput | tuple[torch.FloatTensor]:
        r"""
        image_embeds (`torch.FloatTensor` of shape `(batch_size, num_patches, hidden_size)`, *optional*):
            Optionally, instead of passing `pixel_values`, you can choose to directly pass an embedded representation.
            This is useful if you want more control over how to convert `pixel_values` into patch embeddings.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Binary classification labels.

        Examples:

        ```python
        >>> from transformers import ViltProcessor, ViltForImagesAndTextClassification
        >>> import httpx
        >>> from io import BytesIO
        >>> from PIL import Image

        >>> url_1 = "https://lil.nlp.cornell.edu/nlvr/exs/ex0_0.jpg"
        >>> with httpx.stream("GET", url_1) as response:
        ...     image_1 = Image.open(BytesIO(response.read()))

        >>> url_2 = "https://lil.nlp.cornell.edu/nlvr/exs/ex0_1.jpg"
        >>> with httpx.stream("GET", url_2) as response:
        ...     image_2 = Image.open(BytesIO(response.read()))

        >>> text = "The left image contains twice the number of dogs as the right image."

        >>> processor = ViltProcessor.from_pretrained("dandelin/vilt-b32-finetuned-nlvr2")
        >>> model = ViltForImagesAndTextClassification.from_pretrained("dandelin/vilt-b32-finetuned-nlvr2")

        >>> # prepare inputs
        >>> encoding = processor([image_1, image_2], text, return_tensors="pt")

        >>> # forward pass
        >>> outputs = model(input_ids=encoding.input_ids, pixel_values=encoding.pixel_values.unsqueeze(0))
        >>> logits = outputs.logits
        >>> idx = logits.argmax(-1).item()
        >>> print("Predicted answer:", model.config.id2label[idx])
        Predicted answer: True
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if pixel_values is not None and pixel_values.ndim == 4:
            # add dummy num_images dimension
            pixel_values = pixel_values.unsqueeze(1)

        if image_embeds is not None and image_embeds.ndim == 3:
            # add dummy num_images dimension
            image_embeds = image_embeds.unsqueeze(1)

        num_images = pixel_values.shape[1] if pixel_values is not None else None
        if num_images is None:
            num_images = image_embeds.shape[1] if image_embeds is not None else None
        if num_images != self.config.num_images:
            raise ValueError(
                "Make sure to match the number of images in the model with the number of images in the input."
            )
        pooler_outputs = []
        hidden_states = [] if output_hidden_states else None
        attentions = [] if output_attentions else None
        for i in range(num_images):
            # forward every image through the model
            outputs = self.vilt(
                input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
                pixel_values=pixel_values[:, i, :, :, :] if pixel_values is not None else None,
                pixel_mask=pixel_mask[:, i, :, :] if pixel_mask is not None else None,
                inputs_embeds=inputs_embeds,
                image_embeds=image_embeds[:, i, :, :] if image_embeds is not None else None,
                image_token_type_idx=i + 1,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )
            pooler_output = outputs.pooler_output if return_dict else outputs[1]
            pooler_outputs.append(pooler_output)
            if output_hidden_states:
                hidden_states.append(outputs.hidden_states)
            if output_attentions:
                attentions.append(outputs.attentions)

        pooled_output = torch.cat(pooler_outputs, dim=-1)
        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()
            # move labels to correct device to enable PP
            labels = labels.to(logits.device)
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        if not return_dict:
            output = (logits, hidden_states, attentions)
            return ((loss,) + output) if loss is not None else output

        return ViltForImagesAndTextClassificationOutput(
            loss=loss,
            logits=logits,
            hidden_states=hidden_states,
            attentions=attentions,
        )