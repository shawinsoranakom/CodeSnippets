def forward(
        self,
        pixel_values: torch.Tensor | None = None,
        noise: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        interpolate_pos_encoding: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | HieraForPreTrainingOutput:
        r"""
        noise (`torch.FloatTensor` of shape `(batch_size, num_mask_units)`, *optional*):
            Mainly used for testing purposes to control randomness and maintain the reproducibility

        Examples:
        ```python
        >>> from transformers import AutoImageProcessor, HieraForPreTraining
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/hiera-tiny-224-mae-hf")
        >>> model = HieraForPreTraining.from_pretrained("facebook/hiera-tiny-224-mae-hf")

        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> logits = outputs.logits
        >>> loss = outputs.loss
        >>> print(list(logits.shape))
        [1, 196, 768]
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        outputs = self.hiera(
            pixel_values,
            noise=noise,
            output_attentions=output_attentions,
            output_hidden_states=True,
            interpolate_pos_encoding=interpolate_pos_encoding,
            return_dict=return_dict,
        )

        feature_maps = outputs[-1]
        bool_masked_pos = outputs[1]
        ids_to_restore = outputs[2]
        # Take only the query pooled and last hidden states
        feature_maps = feature_maps[1 : self.hiera.config.num_query_pool + 1] + (feature_maps[-1],)
        fused_hidden_states = self.multiscale_fusion(feature_maps)
        fused_hidden_states = self.encoder_norm(fused_hidden_states)

        # Reconstruct pixel values
        logits, bool_masked_pos = self.decoder(
            fused_hidden_states,
            bool_masked_pos=bool_masked_pos,
            output_attentions=output_attentions,
        )

        loss = self.forward_loss(pixel_values, logits, bool_masked_pos)

        if not return_dict:
            output = (logits, bool_masked_pos, ids_to_restore)
            if output_hidden_states:
                output = output + (outputs[3],)
            if output_attentions:
                output = output + (outputs[4],)
            if output_hidden_states:
                output = output + (outputs[-1],)
            return ((loss,) + output) if loss is not None else output

        return HieraForPreTrainingOutput(
            loss=loss,
            logits=logits,
            bool_masked_pos=bool_masked_pos,
            ids_restore=ids_to_restore,
            hidden_states=outputs.hidden_states if output_hidden_states else None,
            attentions=outputs.attentions,
            reshaped_hidden_states=outputs.reshaped_hidden_states if output_hidden_states else None,
        )