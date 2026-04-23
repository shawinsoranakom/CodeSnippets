def forward(
        self,
        vision_features,
        class_features,
        task_features,
        task_mask,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        **kwargs,
    ):
        """
        Args:
            vision_features (`torch.FloatTensor`): The sequence of vision features. shape depends on the vision
                backbone.
            class_features (`torch.FloatTensor`): The sequence of class features of shape
                `(class_sequence_length, batch_size, class_embed_dim)`.
            task_features (`torch.FloatTensor`): The sequence of task features of shape
                `(task_sequence_length, batch_size, decoder_hidden_dim)`.
            task_mask (`torch.LongTensor`): The mask for the task features of shape `(batch_size, task_sequence_length)`.
            output_attentions (`bool`, *optional*): Whether or not to return the attentions tensors of all attention
                layers. See `attentions` under returned tensors for more detail.
            output_hidden_states (`bool`, *optional*): Whether or not to return the hidden states of all layers. See
                `hidden_states` under returned tensors for more detail.
            return_dict (`bool`, *optional*): Whether or not to return a [`~file_utils.ModelOutput`] instead of a plain
                tuple.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        vision_features, vision_shapes, vision_shapes_list, level_start_index = self._get_encoder_input(
            vision_features
        )

        # todo add denoising for training
        denoise_embeddings, denoise_bboxes, key_padding_mask = None, None, None
        batch_size = task_mask.shape[0]

        # compose attn_mask for vision_emb and task_emb fusion
        task_features = self.task_encoder(task_features)
        if self.task_project is not None:
            task_features = self.task_project(task_features)
        src_key_mask = (task_mask == 0).detach()
        attn_mask_len = self.num_queries
        fusion_size = attn_mask_len + task_features.shape[0]
        key_padding_mask = torch.zeros([batch_size, fusion_size], dtype=torch.bool).to(task_features.device)
        key_padding_mask[:, attn_mask_len:] = src_key_mask
        decoder_embeddings, reference_points, encoder_bboxes, encoder_class_similarity, init_reference_points = (
            self._get_decoder_input(
                vision_features, tuple(vision_shapes_list), class_features, denoise_embeddings, denoise_bboxes
            )
        )
        attention_mask = create_bidirectional_mask(
            config=self.config,
            inputs_embeds=torch.ones_like(key_padding_mask, dtype=decoder_embeddings.dtype)[..., None],
            attention_mask=~key_padding_mask,
        )

        all_hidden_states = () if output_hidden_states else None
        all_attns = () if output_attentions else None
        all_self_attns = () if output_attentions else None
        all_cross_attns = () if output_attentions else None
        predicted_class_features = decoder_embeddings

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (predicted_class_features,)
        decoder_bboxes = []
        decoder_classes = []
        last_refined_bbox = None
        reference_points = reference_points.sigmoid()
        for i, layer in enumerate(self.layers):
            predicted_class_features, task_features, self_attention, cross_attention = layer(
                predicted_class_features,
                task_features,
                reference_points,
                vision_features,
                vision_shapes,
                vision_shapes_list,
                level_start_index=level_start_index,
                attention_mask=attention_mask,
                query_position=self.query_position_head(reference_points),
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
            )
            if output_attentions:
                all_self_attns = all_self_attns + (self_attention,)
                all_cross_attns = all_cross_attns + (cross_attention,)
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (predicted_class_features,)

            refined_bbox = torch.sigmoid(
                self.decoder_bbox_head[i](predicted_class_features) + _inverse_sigmoid(reference_points)
            )
            original_class_projected = self.decoder_class_head[i](class_features).permute(1, 2, 0)
            if self.training:
                decoder_classes.append(
                    get_class_similarity(
                        class_distance_type=self.class_distance_type,
                        cls_feature=predicted_class_features,
                        class_proj=original_class_projected,
                    )
                )
                if i == 0:
                    decoder_bboxes.append(refined_bbox)
                else:
                    decoder_bboxes.append(
                        torch.sigmoid(
                            self.decoder_bbox_head[i](predicted_class_features) + _inverse_sigmoid(last_refined_bbox)
                        )
                    )
            elif i == self.decoder_num_layers - 1:
                decoder_classes.append(
                    get_class_similarity(self.class_distance_type, predicted_class_features, original_class_projected)
                )
                decoder_bboxes.append(refined_bbox)
                break
            last_refined_bbox = refined_bbox
            reference_points = refined_bbox.detach() if self.training else refined_bbox
        if output_attentions:
            all_attns += (all_self_attns, all_cross_attns)

        last_hidden_state = predicted_class_features
        decoder_bboxes = torch.stack(decoder_bboxes)
        decoder_classes = torch.stack(decoder_classes)

        if not return_dict:
            return (
                last_hidden_state,
                all_hidden_states,
                all_attns,
                decoder_bboxes,
                decoder_classes,
                encoder_bboxes,
                encoder_class_similarity,
                init_reference_points,
                reference_points,
            )

        return OmDetTurboDecoderOutput(
            last_hidden_state=last_hidden_state,
            hidden_states=all_hidden_states,
            attentions=all_attns,
            decoder_coords=decoder_bboxes,
            decoder_classes=decoder_classes,
            encoder_coord_logits=encoder_bboxes,
            encoder_class_logits=encoder_class_similarity,
            init_reference_points=init_reference_points,
            intermediate_reference_points=reference_points,
        )