def forward(
        self,
        pixel_values: Tensor,
        mask_labels: list[Tensor] | None = None,
        class_labels: list[Tensor] | None = None,
        patch_offsets: list[Tensor] | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> EomtForUniversalSegmentationOutput:
        r"""
        mask_labels (`list[torch.Tensor]`, *optional*):
            list of mask labels of shape `(num_labels, height, width)` to be fed to a model
        class_labels (`list[torch.LongTensor]`, *optional*):
            list of target class labels of shape `(num_labels, height, width)` to be fed to a model. They identify the
            labels of `mask_labels`, e.g. the label of `mask_labels[i][j]` if `class_labels[i][j]`.
        patch_offsets (`list[torch.Tensor]`, *optional*):
            list of tuples indicating the image index and start and end positions of patches for semantic segmentation.
        """

        masks_queries_logits_per_layer, class_queries_logits_per_layer = (), ()
        attention_mask = None

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")

        hidden_states = self.embeddings(pixel_values)

        for idx, layer_module in enumerate(self.layers):
            if idx == self.num_hidden_layers - self.config.num_blocks:
                query = self.query.weight[None, :, :].expand(hidden_states.shape[0], -1, -1).to(hidden_states.device)
                hidden_states = torch.cat((query, hidden_states), dim=1)

            if idx >= self.num_hidden_layers - self.config.num_blocks and (
                self.training or self.attn_mask_probs[idx - self.num_hidden_layers + self.config.num_blocks] > 0
            ):
                norm_hidden_states = self.layernorm(hidden_states)
                masks_queries_logits, class_queries_logits = self.predict(norm_hidden_states)

                masks_queries_logits_per_layer += (masks_queries_logits,)
                class_queries_logits_per_layer += (class_queries_logits,)

                attention_mask = torch.ones(
                    hidden_states.shape[0],
                    hidden_states.shape[1],
                    hidden_states.shape[1],
                    device=hidden_states.device,
                    dtype=torch.bool,
                )

                interpolated_logits = F.interpolate(masks_queries_logits, size=self.grid_size, mode="bilinear")
                interpolated_logits = interpolated_logits.view(
                    interpolated_logits.size(0), interpolated_logits.size(1), -1
                )

                num_query_tokens = self.config.num_queries
                encoder_start_tokens = num_query_tokens + self.embeddings.num_prefix_tokens

                # Set attention mask for queries to focus on encoder tokens based on interpolated logits
                attention_mask[:, :num_query_tokens, encoder_start_tokens:] = interpolated_logits > 0

                # Disable attention mask for random query tokens.
                attention_mask = self._disable_attention_mask(
                    attention_mask,
                    prob=self.attn_mask_probs[idx - self.num_hidden_layers + self.config.num_blocks],
                    num_query_tokens=num_query_tokens,
                    encoder_start_tokens=encoder_start_tokens,
                    device=attention_mask.device,
                )

                # Expand attention mask to 4d mask.
                attention_mask = attention_mask[:, None, ...].expand(-1, self.config.num_attention_heads, -1, -1)
                attention_mask = attention_mask.float().masked_fill(~attention_mask, -1e9)

            hidden_states = layer_module(hidden_states, attention_mask)

        sequence_output = self.layernorm(hidden_states)

        masks_queries_logits, class_queries_logits = self.predict(sequence_output)
        masks_queries_logits_per_layer += (masks_queries_logits,)
        class_queries_logits_per_layer += (class_queries_logits,)

        loss = None
        if mask_labels is not None and class_labels is not None:
            loss = 0.0
            for masks_queries_logits, class_queries_logits in zip(
                masks_queries_logits_per_layer, class_queries_logits_per_layer
            ):
                loss_dict = self.get_loss_dict(
                    masks_queries_logits=masks_queries_logits,
                    class_queries_logits=class_queries_logits,
                    mask_labels=mask_labels,
                    class_labels=class_labels,
                    auxiliary_predictions=None,
                )
                loss += self.get_loss(loss_dict)

        return EomtForUniversalSegmentationOutput(
            loss=loss,
            masks_queries_logits=masks_queries_logits,
            class_queries_logits=class_queries_logits,
            last_hidden_state=sequence_output,
            patch_offsets=patch_offsets,
        )