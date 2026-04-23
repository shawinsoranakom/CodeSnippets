def forward(
        self,
        descriptors: torch.Tensor,
        keypoints: torch.Tensor,
        attention_mask: torch.Tensor,
        output_hidden_states: bool | None = False,
        output_attentions: bool | None = False,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor] | None, tuple[torch.Tensor] | None]:
        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (descriptors,)

        batch_size, num_keypoints, descriptor_dim = descriptors.shape

        # Self attention block
        attention_output, self_attentions = self.self_attention(
            descriptors,
            position_embeddings=keypoints,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
        )
        intermediate_states = torch.cat([descriptors, attention_output], dim=-1)
        output_states = self.self_mlp(intermediate_states)
        self_attention_descriptors = descriptors + output_states

        if output_hidden_states:
            self_attention_hidden_states = (intermediate_states, output_states)

        # Reshape hidden_states to group by image_pairs :
        #   (batch_size, num_keypoints, descriptor_dim) -> (batch_size, 2, num_keypoints, descriptor_dim)
        # Flip dimension 1 to perform cross attention :
        #   (image0, image1) -> (image1, image0)
        # Reshape back to original shape :
        #   (batch_size, 2, num_keypoints, descriptor_dim) -> (batch_size, num_keypoints, descriptor_dim)
        encoder_hidden_states = (
            self_attention_descriptors.reshape(-1, 2, num_keypoints, descriptor_dim)
            .flip(1)
            .reshape(batch_size, num_keypoints, descriptor_dim)
        )
        # Same for mask
        encoder_attention_mask = (
            attention_mask.reshape(-1, 2, 1, 1, num_keypoints).flip(1).reshape(batch_size, 1, 1, num_keypoints)
            if attention_mask is not None
            else None
        )

        # Cross attention block
        cross_attention_output, cross_attentions = self.cross_attention(
            self_attention_descriptors,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            output_attentions=output_attentions,
        )
        cross_intermediate_states = torch.cat([self_attention_descriptors, cross_attention_output], dim=-1)
        cross_output_states = self.cross_mlp(cross_intermediate_states)
        descriptors = self_attention_descriptors + cross_output_states

        if output_hidden_states:
            cross_attention_hidden_states = (cross_intermediate_states, cross_output_states)
            all_hidden_states = (
                all_hidden_states
                + (self_attention_descriptors.reshape(batch_size, num_keypoints, descriptor_dim),)
                + self_attention_hidden_states
                + (descriptors.reshape(batch_size, num_keypoints, descriptor_dim),)
                + cross_attention_hidden_states
            )

        if output_attentions:
            all_attentions = all_attentions + (self_attentions,) + (cross_attentions,)

        return descriptors, all_hidden_states, all_attentions