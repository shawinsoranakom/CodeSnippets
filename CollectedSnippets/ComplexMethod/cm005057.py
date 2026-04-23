def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        input_ids_masked: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        codebook_pixel_values: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        bool_masked_pos: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        image_attention_mask: torch.Tensor | None = None,
        skip_unmasked_multimodal_encoder: bool | None = None,
        mlm_labels: torch.Tensor | None = None,
        mim_labels: torch.Tensor | None = None,
        itm_labels: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool = True,
        return_dict: bool | None = None,
        return_loss: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | FlavaForPreTrainingOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, text_seq_len)`):
            Indices of input sequence tokens in the vocabulary. Indices can be obtained using [`AutoTokenizer`]. See
            [`PreTrainedTokenizer.encode`] and [`PreTrainedTokenizer.__call__`] for details. [What are input
            IDs?](../glossary#input-ids)
        input_ids_masked (`torch.LongTensor` of shape `(batch_size, text_seq_len)`):
            Indices of input sequence tokens in the vocabulary. These ones are the masked version of the original task
            to be used with MLM. Indices can be obtained using [`AutoTokenizer`] along with
            [`DataCollatorForMaskedLanguageModeling`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details. [What are input IDs?](../glossary#input-ids)
        codebook_pixel_values (`torch.FloatTensor` of shape `(batch_size, num_image_patches, patch_size, patch_size, 3)`, *optional*):
            Pixel values for image patches that are used to compute the image codebook labels for masked image modeling.
        token_type_ids (`torch.LongTensor` of shape `(batch_size, text_seq_len)`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`:
            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.
            [What are token type IDs?](../glossary#token-type-ids)
        bool_masked_pos (`torch.BoolTensor` of shape `(batch_size, image_num_patches)`):
            Boolean masked positions. Indicates which patches are masked (1) and which aren't (0).
        image_attention_mask (`torch.FloatTensor` of shape `(batch_size, image_num_patches)`, *optional*):
            Mask to avoid performing attention on padding token indices specifically for images. Mask values selected
            in `[0, 1]`:
            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.
            [What are attention masks?](../glossary#attention-mask)
        skip_unmasked_multimodal_encoder (*bool*, *optional*):
            Skip any calculations for multimodal encoder for unmasked inputs. FLAVA pretraining doesn't need unmasked
            multimodal embeddings or outputs as of now.
        mlm_labels (`torch.LongTensor` of shape `(batch_size, text_seq_len)`, *optional*):
            Labels for computing the left-to-right language and multimodal masked modeling loss (next word prediction).
            Indices should be in `[-100, 0, ..., text_config.vocab_size - 1]` (see `input_ids` docstring). Tokens with
            indices set to `-100` are ignored (masked), the loss is only computed for the tokens with labels in `[0,
            ..., text_config.vocab_size - 1]`.
        mim_labels (`torch.LongTensor` of shape `(batch_size, image_num_patches)`, *optional*):
            Labels for computing the image and multimodal masked modeling loss. Indices should be in `[-100, 0, ...,
            image_config.vocab_size - 1]`. Tokens with indices set to `-100` are ignored (masked), the loss is only
            computed for the tokens with labels in `[0, ..., image_config.vocab_size - 1]`. If not passed, they are
            generated automatically using the image codebook assigned to the model. By default, it uses
            [`FlavaImageCodebook`]. See [`FlavaImageCodebook`] to understand how to generate mim_labels.
        itm_labels (`torch.LongTensor` of shape `(batch_size, 1)`, *optional*):
            Labels for computing the image-text matching loss. 0 means the pairs don't match and 1 means they match.
            The pairs with 0 will be skipped for calculation of MMM and global contrastive losses as well.
        return_loss (`bool`, *optional*, default to None):
            Whether to return calculated loss or not.

        Examples:
        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import FlavaForPreTraining, AutoProcessor

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> model = FlavaForPreTraining.from_pretrained("facebook/flava-full")
        >>> processor = AutoProcessor.from_pretrained("facebook/flava-full")

        >>> text = ["a photo of a cat"]

        >>> inputs = processor(
        ...     images=[image],
        ...     text=text,
        ...     return_masks=True,
        ...     return_codebook_pixels=True,
        ...     padding=True,
        ...     max_length=77,
        ...     return_tensors="pt",
        ... )


        >>> output = model(**inputs)
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        return_loss = return_loss if return_loss is not None else self.config.return_loss

        skip_unmasked_multimodal_encoder = (
            skip_unmasked_multimodal_encoder
            if skip_unmasked_multimodal_encoder is not None
            else self.skip_unmasked_multimodal_encoder
        )

        if input_ids_masked is None and input_ids is not None:
            logger.warning(
                "`input_ids_masked` isn't passed which means MLM loss won't be calculated correctlySetting it to"
                " `input_ids` so that model can work. Please pass it if this is unintentional. This is usually OKAY if"
                " you are doing inference on unmasked text..."
            )
            input_ids_masked = input_ids

        flava_output = self.flava(
            input_ids=input_ids,
            pixel_values=pixel_values,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            image_attention_mask=image_attention_mask,
            # Don't need unmasked multimodal embedding for anything so skip it
            # NOTE: ITM uses masked version
            skip_multimodal_encoder=skip_unmasked_multimodal_encoder,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            # Pass true to have deterministic outputs
            return_dict=True,
        )

        flava_masked_output = self.flava(
            input_ids=input_ids_masked,
            pixel_values=pixel_values,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            image_attention_mask=image_attention_mask,
            bool_masked_pos=bool_masked_pos,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=True,
        )

        pos_mask = None

        image_embeddings = flava_output.image_embeddings
        text_embeddings = flava_output.text_embeddings
        image_masked_embeddings = flava_masked_output.image_embeddings
        text_masked_embeddings = flava_masked_output.text_embeddings
        multimodal_masked_embeddings = flava_masked_output.multimodal_embeddings

        total_loss = mim_loss = mlm_loss = mmm_text_loss = mmm_image_loss = gc_loss = itm_loss = None
        mim_logits = mlm_logits = mmm_text_logits = mmm_image_logits = None
        itm_logits = logits_per_image = logits_per_text = None

        # Calculate mim_labels if necessary from the image_codebook
        if image_masked_embeddings is not None or multimodal_masked_embeddings is not None:
            if mim_labels is None and return_loss:
                if self.image_codebook is None:
                    raise RuntimeError(
                        "`return_loss` is set to True but the image codebook is not initialized and no `mim_labels` "
                        " have been passed. Reinstantiate the model with `init_codebook` set to True or "
                        "pass in your custom `mim_labels`"
                    )
                if codebook_pixel_values is None:
                    raise ValueError(
                        "`codebook_pixel_value` are required to generate `mim_labels` if loss is expected. "
                        "Call `AutoProcessor` with `return_codebook_pixels` set to True"
                    )
                mim_labels = self.image_codebook.get_codebook_indices(codebook_pixel_values)
        # Unimodal MIM Loss
        # If multimodal embeddings are present, we will calculate MMM loss
        if self.mim_weight > 0 and image_masked_embeddings is not None and multimodal_masked_embeddings is None:
            sequence_for_image = image_masked_embeddings

            if mim_labels is not None:
                mim_labels = self._resize_to_2d(mim_labels)
                bool_masked_pos = self._resize_to_2d(bool_masked_pos)
                mim_labels[bool_masked_pos.ne(True)] = self.ce_ignore_index

                sequence_for_image = sequence_for_image[:, -mim_labels.size(1) :, :]
                masked_tokens = mim_labels.ne(self.ce_ignore_index)
                mim_labels_filtered = mim_labels[masked_tokens]
                sequence_for_image = sequence_for_image[masked_tokens, :]
                mim_logits = self.mim_head(sequence_for_image)
                if return_loss:
                    mim_loss = nn.functional.cross_entropy(
                        mim_logits.view(-1, self.image_vocab_size), mim_labels_filtered.view(-1)
                    )
                    mim_loss *= self.mim_weight
            else:
                mim_logits = self.mim_head(sequence_for_image)

        # Unimodal MLM Loss
        if self.mlm_weight > 0 and text_masked_embeddings is not None and multimodal_masked_embeddings is None:
            sequence_for_text = text_masked_embeddings
            if mlm_labels is not None:
                mlm_labels = self._resize_to_2d(mlm_labels)
                sequence_for_text = sequence_for_text[:, -mlm_labels.size(1) :, :]
                masked_tokens = mlm_labels.ne(self.ce_ignore_index)
                mlm_labels_filtered = mlm_labels[masked_tokens]
                sequence_for_text = sequence_for_text[masked_tokens, :]
                mlm_logits = self.mlm_head(sequence_for_text)
                if return_loss:
                    mlm_loss = nn.functional.cross_entropy(
                        mlm_logits.view(-1, self.text_vocab_size), mlm_labels_filtered.view(-1)
                    )
                    mlm_loss *= self.mlm_weight
            else:
                mlm_logits = self.mlm_head(sequence_for_text)

        # ITM Loss
        if self.itm_weight > 0 and multimodal_masked_embeddings is not None:
            itm_logits = self.itm_head(multimodal_masked_embeddings)

            if itm_labels is not None:
                pos_pairs = itm_labels.ne(0)
                pos_mask = torch.where(pos_pairs.any(), pos_pairs, pos_pairs.new([True]))
                if return_loss:
                    itm_loss = nn.functional.cross_entropy(itm_logits, itm_labels)
                    itm_loss *= self.itm_weight

                if multimodal_masked_embeddings is not None:
                    multimodal_masked_embeddings = multimodal_masked_embeddings[pos_mask]

                if mlm_labels is not None:
                    mlm_labels = mlm_labels[pos_mask]

                if mim_labels is not None:
                    mim_labels = mim_labels[pos_mask]
                    bool_masked_pos = bool_masked_pos[pos_mask]

        # MMM Image Loss
        if multimodal_masked_embeddings is not None and self.mmm_image_weight > 0:
            sequence_for_image = multimodal_masked_embeddings
            end_index = image_masked_embeddings.size(1) - 1
            sequence_for_image = sequence_for_image[:, 2 : 2 + end_index, :]

            if mim_labels is not None:
                mim_labels = self._resize_to_2d(mim_labels)
                bool_masked_pos = self._resize_to_2d(bool_masked_pos)
                mim_labels[bool_masked_pos.ne(True)] = self.ce_ignore_index

                masked_tokens = mim_labels.ne(self.ce_ignore_index)
                mim_labels_filtered = mim_labels[masked_tokens]
                sequence_for_image = sequence_for_image[masked_tokens, :]
                mmm_image_logits = self.mmm_image_head(sequence_for_image)
                if return_loss:
                    mmm_image_loss = nn.functional.cross_entropy(
                        mmm_image_logits.view(-1, self.image_vocab_size), mim_labels_filtered.view(-1)
                    )
                    mmm_image_loss *= self.mmm_image_weight
            else:
                mmm_image_logits = self.mmm_image_head(sequence_for_image)

        # MMM Text Loss
        if multimodal_masked_embeddings is not None and self.mmm_text_weight > 0:
            sequence_for_text = multimodal_masked_embeddings
            sequence_for_text = sequence_for_text[:, -text_masked_embeddings.size(1) :, :]

            if mlm_labels is not None:
                mlm_labels = self._resize_to_2d(mlm_labels)
                masked_tokens = mlm_labels.ne(self.ce_ignore_index)
                mlm_labels_filtered = mlm_labels[masked_tokens]
                sequence_for_text = sequence_for_text[masked_tokens, :]
                mmm_text_logits = self.mmm_text_head(sequence_for_text)
                if return_loss:
                    mmm_text_loss = nn.functional.cross_entropy(
                        mmm_text_logits.view(-1, self.text_vocab_size), mlm_labels_filtered.view(-1)
                    )
                    mmm_text_loss *= self.mmm_text_weight
            else:
                mmm_text_logits = self.mmm_text_head(sequence_for_text)

        # Global Contrastive Loss
        if image_embeddings is not None and text_embeddings is not None and self.global_contrastive_weight > 0:
            text_embedding = self.flava.text_projection(text_embeddings[:, 0, :])
            text_embedding = nn.functional.normalize(text_embedding, dim=-1)

            image_embedding = self.flava.image_projection(image_embeddings[:, 0, :])
            image_embedding = nn.functional.normalize(image_embedding, dim=-1)

            if self.training:
                self.flava.logit_scale.data.clamp_(LOGIT_SCALE_CLAMP_MIN, LOGIT_SCALE_CLAMP_MAX)

            logits_per_image, logits_per_text, gc_labels = self.global_contrastive_head(
                image_embedding, text_embedding, self.flava.logit_scale
            )

            # Apply ITM negative mask if any
            if pos_mask is not None:
                logits_per_image = logits_per_image[pos_mask]
                logits_per_text = logits_per_text[pos_mask]
                gc_labels = gc_labels[pos_mask]

            if return_loss:
                gc_loss_image = nn.functional.cross_entropy(logits_per_image, gc_labels)
                gc_loss_text = nn.functional.cross_entropy(logits_per_text, gc_labels)
                gc_loss = (gc_loss_image + gc_loss_text) / 2
                gc_loss *= self.global_contrastive_weight

        flava_losses = FlavaLosses(
            mim=mim_loss,
            mlm=mlm_loss,
            itm=itm_loss,
            global_contrastive=gc_loss,
            mmm_image=mmm_image_loss,
            mmm_text=mmm_text_loss,
        )

        if return_loss and not flava_losses.all_none():
            total_loss = sum(loss if loss is not None else 0 for loss in flava_losses.values())

        if not return_dict:
            output = (
                image_embeddings,
                flava_output.image_output.to_tuple() if flava_output.image_output is not None else None,
                text_embeddings,
                flava_output.text_output.to_tuple() if flava_output.text_output is not None else None,
                flava_output.multimodal_embeddings,
                flava_output.multimodal_output.to_tuple() if flava_output.multimodal_output is not None else None,
                image_masked_embeddings,
                flava_masked_output.image_output.to_tuple() if flava_masked_output.image_output is not None else None,
                text_masked_embeddings,
                flava_masked_output.text_output.to_tuple() if flava_masked_output.text_output is not None else None,
                multimodal_masked_embeddings,
                flava_masked_output.multimodal_output.to_tuple()
                if flava_masked_output.multimodal_output is not None
                else None,
                mim_logits,
                mlm_logits,
                itm_logits,
                logits_per_image,
                logits_per_image,
                mmm_image_logits,
                mmm_text_logits,
            )
            if return_loss and not flava_losses.all_none():
                output = (
                    total_loss,
                    flava_losses,
                ) + output

            # Filter None as transformer by default won't handle it
            return tuple(x for x in output if x is None)

        return FlavaForPreTrainingOutput(
            loss=total_loss,
            loss_info=flava_losses,
            image_embeddings=image_embeddings,
            image_output=flava_output.image_output,
            text_embeddings=text_embeddings,
            text_output=flava_output.text_output,
            multimodal_embeddings=flava_output.multimodal_embeddings,
            multimodal_output=flava_output.multimodal_output,
            image_masked_embeddings=image_masked_embeddings,
            image_masked_output=flava_masked_output.image_output,
            text_masked_embeddings=text_masked_embeddings,
            text_masked_output=flava_masked_output.text_output,
            multimodal_masked_embeddings=multimodal_masked_embeddings,
            multimodal_masked_output=flava_masked_output.multimodal_output,
            mim_logits=mim_logits,
            mlm_logits=mlm_logits,
            itm_logits=itm_logits,
            contrastive_logits_per_image=logits_per_image,
            contrastive_logits_per_text=logits_per_text,
            mmm_image_logits=mmm_image_logits,
            mmm_text_logits=mmm_text_logits,
        )