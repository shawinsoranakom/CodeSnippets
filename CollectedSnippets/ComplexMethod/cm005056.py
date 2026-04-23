def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        bool_masked_pos: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        image_attention_mask: torch.Tensor | None = None,
        skip_multimodal_encoder: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool = True,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | FlavaModelOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, image_num_patches + text_seq_len)`):
            Indices of input sequence tokens in the vocabulary. Indices can be obtained using [`AutoTokenizer`]. See
            [`PreTrainedTokenizer.encode`] and [`PreTrainedTokenizer.__call__`] for details. [What are input
            IDs?](../glossary#input-ids)
        token_type_ids (`torch.LongTensor` of shape `(batch_size, image_num_patches + text_seq_len)`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`:
            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.
            [What are token type IDs?](../glossary#token-type-ids)
        bool_masked_pos (`torch.BoolTensor` of shape `(batch_size, image_num_patches)`):
            Boolean masked positions. Indicates which patches are masked (1) and which aren't (0).
        image_attention_mask (`torch.Tensor` of shape `(batch_size, image_num_patches)`, *optional*):
            Mask to avoid performing attention on padding pixel values for image inputs. Mask values selected in `[0, 1]`:
            - 1 for pixel values that are real (i.e., **not masked**),
            - 0 for pixel values that are padding (i.e., **masked**).
        skip_multimodal_encoder (*bool*, *optional*):
            Skip any calculations for multimodal encoder. Useful if multimodal encoding is not going to be used.

        Examples:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoProcessor, FlavaModel

        >>> model = FlavaModel.from_pretrained("facebook/flava-full")
        >>> processor = AutoProcessor.from_pretrained("facebook/flava-full")

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> inputs = processor(text=["a photo of a cat"], images=image, return_tensors="pt", padding=True)

        >>> outputs = model(**inputs)

        >>> image_embeddings = outputs.image_embeddings
        >>> text_embeddings = outputs.text_embeddings
        >>> multimodal_embeddings = outputs.multimodal_embeddings

        >>> outputs.image_embeddings.shape
        torch.Size([1, 197, 768])

        >>> text_embeddings.shape
        torch.Size([1, 7, 768])

        >>> multimodal_embeddings.shape
        torch.Size([1, 205, 768])
        ```
        """

        return_dict = return_dict if return_dict is not None else self.config.return_dict
        if not output_hidden_states:
            raise ValueError("FLAVA model requires hidden states to work. Please set `output_hidden_states=True`")
        image_embeddings = None
        image_states = None
        image_mm_projection = None
        image_output = None
        if pixel_values is not None:
            image_output = self.image_model(
                pixel_values=pixel_values,
                bool_masked_pos=bool_masked_pos,
                attention_mask=image_attention_mask,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )
            image_embeddings, image_states = image_output[0], image_output[2]
            # Note that these states don't use final layernorm in the transformer model
            image_mm_projection = self.image_to_mm_projection(image_states[-1])

        text_embeddings = None
        text_states = None
        text_mm_projection = None
        text_output = None
        if input_ids is not None:
            text_output = self.text_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                position_ids=position_ids,
                token_type_ids=token_type_ids,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )

            text_embeddings, text_states = text_output[0], text_output[2]
            # Note that these states don't use final layernorm in the transformer model
            text_mm_projection = self.text_to_mm_projection(text_states[-1])

        multimodal_embeddings = None
        multimodal_output = None
        if image_mm_projection is not None and text_mm_projection is not None and not skip_multimodal_encoder:
            if attention_mask is not None:
                batch_size, seq_len, _ = image_mm_projection.shape
                if self.multimodal_model.use_cls_token:
                    seq_len += 1
                attention_mask_image = torch.ones(batch_size, seq_len, device=image_mm_projection.device)
                attention_multimodal = torch.cat([attention_mask_image, attention_mask], dim=1)
            else:
                attention_multimodal = None
            multimodal_input = torch.cat([image_mm_projection, text_mm_projection], dim=1)
            multimodal_output = self.multimodal_model(
                multimodal_input, attention_mask=attention_multimodal, return_dict=return_dict
            )
            multimodal_embeddings = multimodal_output[0]

        if not return_dict:
            return (
                image_embeddings,
                image_output,
                text_embeddings,
                text_output,
                multimodal_embeddings,
                multimodal_output,
            )

        return FlavaModelOutput(
            image_embeddings=image_embeddings,
            image_output=image_output,
            text_embeddings=text_embeddings,
            text_output=text_output,
            multimodal_embeddings=multimodal_embeddings,
            multimodal_output=multimodal_output,
        )