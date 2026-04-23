def forward(
        self,
        pixel_values: torch.FloatTensor,
        input_ids: torch.LongTensor,
        attention_mask: torch.LongTensor | None = None,
        use_image_text_matching_head: bool | None = False,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | Blip2ImageTextMatchingModelOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Indices of input sequence tokens in the vocabulary of the language model. Input tokens can optionally be
            provided to serve as text prompt, which the language model can continue.

            Indices can be obtained using [`Blip2Processor`]. See [`Blip2Processor.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        use_image_text_matching_head (`bool`, *optional*):
            Whether to return the Image-Text Matching or Contrastive scores.

        Examples:

        ```python
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoProcessor, Blip2ForImageTextRetrieval

        >>> device = "cuda" if torch.cuda.is_available() else "cpu"

        >>> model = Blip2ForImageTextRetrieval.from_pretrained("Salesforce/blip2-itm-vit-g", dtype=torch.float16)
        >>> processor = AutoProcessor.from_pretrained("Salesforce/blip2-itm-vit-g")

        >>> model.to(device)  # doctest: +IGNORE_RESULT

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> text = "two cats laying on a pink blanket"

        >>> inputs = processor(images=image, text=text, return_tensors="pt").to(device, torch.float16)
        >>> itm_out = model(**inputs, use_image_text_matching_head=True)
        >>> logits_per_image = torch.nn.functional.softmax(itm_out.logits_per_image, dim=1)
        >>> probs = logits_per_image.softmax(dim=1)  # we can take the softmax to get the label probabilities

        >>> print(f"{probs[0][0]:.1%} that image 0 is not '{text}'")
        26.9% that image 0 is not 'two cats laying on a pink blanket'

        >>> print(f"{probs[0][1]:.1%} that image 0 is '{text}'")
        73.0% that image 0 is 'two cats laying on a pink blanket'

        >>> texts = ["a photo of a cat", "a photo of a dog"]

        >>> inputs = processor(images=image, text=texts, return_tensors="pt").to(device, torch.float16)
        >>> itc_out = model(**inputs, use_image_text_matching_head=False)
        >>> logits_per_image = itc_out.logits_per_image  # this is the image-text similarity score
        >>> probs = logits_per_image.softmax(dim=1)  # we can take the softmax to get the label probabilities

        >>> print(f"{probs[0][0]:.1%} that image 0 is '{texts[0]}'")
        55.3% that image 0 is 'a photo of a cat'

        >>> print(f"{probs[0][1]:.1%} that image 0 is '{texts[1]}'")
        44.7% that image 0 is 'a photo of a dog'
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        vision_outputs = self.vision_model(
            pixel_values=pixel_values,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        image_embeds = vision_outputs[0]
        image_attention_mask = torch.ones(image_embeds.size()[:-1], dtype=torch.long, device=image_embeds.device)

        if use_image_text_matching_head:
            query_tokens = self.query_tokens.expand(image_embeds.shape[0], -1, -1)
            if self.config.image_token_index is not None:
                input_ids = input_ids[:, self.config.num_query_tokens :]
            else:
                query_attention_mask = torch.ones(
                    query_tokens.size()[:-1], dtype=torch.long, device=query_tokens.device
                )
                attention_mask = torch.cat([query_attention_mask, attention_mask], dim=1)

            query_embeds = self.embeddings(
                input_ids=input_ids,
                query_embeds=query_tokens,
            )

            text_outputs = self.qformer(
                query_embeds=query_embeds,
                query_length=query_tokens.shape[1],
                attention_mask=attention_mask,
                encoder_hidden_states=image_embeds,
                encoder_attention_mask=image_attention_mask,
                return_dict=return_dict,
            )
            text_embeds = text_outputs[0] if not return_dict else text_outputs.last_hidden_state
            text_embeds = text_embeds.to(dtype=self.itm_head.weight.dtype)

            output = self.itm_head(text_embeds[:, : query_tokens.size(1), :])
            logits_per_image = output.mean(dim=1)
            logits_per_text = logits_per_image.t()
        else:
            query_tokens = self.query_tokens.expand(image_embeds.shape[0], -1, -1)
            query_outputs = self.qformer(
                query_embeds=query_tokens,
                encoder_hidden_states=image_embeds,
                encoder_attention_mask=image_attention_mask,
                return_dict=return_dict,
            )
            image_embeds = query_outputs[0] if not return_dict else query_outputs.last_hidden_state
            image_embeds = image_embeds.to(dtype=self.vision_projection.weight.dtype)

            if self.config.image_token_index is not None:
                input_ids = input_ids[:, self.config.num_query_tokens :]
                attention_mask = attention_mask[:, self.config.num_query_tokens :]

            query_embeds = self.embeddings(
                input_ids=input_ids,
            )
            text_outputs = self.qformer(
                query_embeds=query_embeds,
                query_length=0,
                attention_mask=attention_mask,
                return_dict=return_dict,
            )
            question_embeds = text_outputs[0] if not return_dict else text_outputs.last_hidden_state
            question_embeds = question_embeds.to(dtype=self.text_projection.weight.dtype)

            # normalized features
            image_embeds = nn.functional.normalize(self.vision_projection(image_embeds), dim=-1)
            text_embeds = nn.functional.normalize(self.text_projection(question_embeds[:, 0, :]), dim=-1)

            # cosine similarity as logits
            logits_per_image = torch.matmul(image_embeds, text_embeds.t())
            logits_per_image, _ = logits_per_image.max(dim=1)

            logits_per_text = logits_per_image.t()

        if not return_dict:
            output = (logits_per_image, logits_per_text, text_embeds, image_embeds, text_outputs, vision_outputs)
            return output

        return Blip2ImageTextMatchingModelOutput(
            logits_per_image=logits_per_image,
            logits_per_text=logits_per_text,
            text_embeds=text_embeds,
            image_embeds=image_embeds,
            text_model_output=text_outputs,
            vision_model_output=vision_outputs,
        )