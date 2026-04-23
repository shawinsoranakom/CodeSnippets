def forward(
        self,
        descriptors: torch.Tensor,
        mask: torch.Tensor | None = None,
        output_attentions: bool = False,
        output_hidden_states: bool | None = False,
    ) -> tuple[torch.Tensor, tuple | None, tuple | None]:
        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        batch_size, num_keypoints, _ = descriptors.shape
        if output_hidden_states:
            all_hidden_states = all_hidden_states + (descriptors,)

        for gnn_layer, layer_type in zip(self.layers, self.layers_types):
            encoder_hidden_states = None
            encoder_attention_mask = None
            if layer_type == "cross":
                encoder_hidden_states = (
                    descriptors.reshape(-1, 2, num_keypoints, self.hidden_size)
                    .flip(1)
                    .reshape(batch_size, num_keypoints, self.hidden_size)
                )
                encoder_attention_mask = (
                    mask.reshape(-1, 2, 1, 1, num_keypoints).flip(1).reshape(batch_size, 1, 1, num_keypoints)
                    if mask is not None
                    else None
                )

            gnn_outputs = gnn_layer(
                descriptors,
                attention_mask=mask,
                encoder_hidden_states=encoder_hidden_states,
                encoder_attention_mask=encoder_attention_mask,
                output_hidden_states=output_hidden_states,
                output_attentions=output_attentions,
            )
            delta = gnn_outputs[0]

            if output_hidden_states:
                all_hidden_states = all_hidden_states + gnn_outputs[1]
            if output_attentions:
                all_attentions = all_attentions + gnn_outputs[2]

            descriptors = descriptors + delta
        return descriptors, all_hidden_states, all_attentions