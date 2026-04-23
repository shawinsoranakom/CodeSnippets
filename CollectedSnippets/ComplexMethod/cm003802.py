def forward(
        self,
        pixel_values: torch.FloatTensor,
        output_attentions: bool | None = None,
        output_a3_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.FloatTensor] | MgpstrModelOutput:
        r"""
        output_a3_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of a3 modules. See `a3_attentions` under returned tensors
            for more detail.

        Example:

        ```python
        >>> from transformers import (
        ...     MgpstrProcessor,
        ...     MgpstrForSceneTextRecognition,
        ... )
        >>> import httpx
        >>> from io import BytesIO
        >>> from PIL import Image

        >>> # load image from the IIIT-5k dataset
        >>> url = "https://i.postimg.cc/ZKwLg2Gw/367-14.png"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read())).convert("RGB")

        >>> processor = MgpstrProcessor.from_pretrained("alibaba-damo/mgp-str-base")
        >>> pixel_values = processor(images=image, return_tensors="pt").pixel_values

        >>> model = MgpstrForSceneTextRecognition.from_pretrained("alibaba-damo/mgp-str-base")

        >>> # inference
        >>> outputs = model(pixel_values)
        >>> out_strs = processor.batch_decode(outputs.logits)
        >>> out_strs["generated_text"]
        '["ticket"]'
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        mgp_outputs = self.mgp_str(
            pixel_values,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = mgp_outputs[0]

        char_a3_out, char_attention = self.char_a3_module(sequence_output)
        bpe_a3_out, bpe_attention = self.bpe_a3_module(sequence_output)
        wp_a3_out, wp_attention = self.wp_a3_module(sequence_output)

        char_logits = self.char_head(char_a3_out)
        bpe_logits = self.bpe_head(bpe_a3_out)
        wp_logits = self.wp_head(wp_a3_out)

        all_a3_attentions = (char_attention, bpe_attention, wp_attention) if output_a3_attentions else None
        all_logits = (char_logits, bpe_logits, wp_logits)

        if not return_dict:
            outputs = (all_logits, all_a3_attentions) + mgp_outputs[1:]
            return tuple(output for output in outputs if output is not None)
        return MgpstrModelOutput(
            logits=all_logits,
            hidden_states=mgp_outputs.hidden_states,
            attentions=mgp_outputs.attentions,
            a3_attentions=all_a3_attentions,
        )