def forward(
        self,
        inputs: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        labels: torch.Tensor | None = None,
        interpolate_pos_encoding: bool = False,
        return_dict: bool | None = None,
        pixel_values: torch.Tensor | None = None,
        **kwargs,
    ) -> tuple | PerceiverClassifierOutput:
        r"""
        inputs (`torch.FloatTensor`):
            Inputs to the perceiver. Can be anything: images, text, audio, video, etc.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the image classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).

        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, PerceiverForImageClassificationLearned
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("deepmind/vision-perceiver-learned")
        >>> model = PerceiverForImageClassificationLearned.from_pretrained("deepmind/vision-perceiver-learned")

        >>> inputs = image_processor(images=image, return_tensors="pt").pixel_values
        >>> outputs = model(inputs=inputs)
        >>> logits = outputs.logits
        >>> list(logits.shape)
        [1, 1000]

        >>> # model predicts one of the 1000 ImageNet classes
        >>> predicted_class_idx = logits.argmax(-1).item()
        >>> print("Predicted class:", model.config.id2label[predicted_class_idx])
        Predicted class: tabby, tabby cat
        ```"""
        if inputs is not None and pixel_values is not None:
            raise ValueError("You cannot use both `inputs` and `pixel_values`")
        elif inputs is None and pixel_values is not None:
            inputs = pixel_values

        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.perceiver(
            inputs=inputs,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            interpolate_pos_encoding=interpolate_pos_encoding,
            return_dict=return_dict,
        )
        logits = outputs.logits if return_dict else outputs[0]

        loss = None
        if labels is not None:
            loss = self.loss_function(labels, logits, self.config)

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return PerceiverClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            cross_attentions=outputs.cross_attentions,
        )