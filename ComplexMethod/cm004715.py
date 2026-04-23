def forward(
        self,
        pixel_values: torch.FloatTensor,
        output_attentions: bool | None = False,
        output_hidden_states: bool | None = False,
        return_dict: bool | None = True,
    ) -> tuple | BaseModelOutput:
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        batch_size = pixel_values.shape[0]
        num_blocks = len(self.block)
        hidden_states = pixel_values
        for idx, (embedding_layer, block_layer) in enumerate(zip(self.patch_embeddings, self.block)):
            # first, obtain patch embeddings
            hidden_states, height, width = embedding_layer(hidden_states)
            # second, send embeddings through blocks
            for block in block_layer:
                layer_outputs = block(hidden_states, height, width, output_attentions)
                hidden_states = layer_outputs[0]
                if output_attentions:
                    all_self_attentions = all_self_attentions + (layer_outputs[1],)
                if output_hidden_states:
                    all_hidden_states = all_hidden_states + (hidden_states,)
            if idx != num_blocks - 1:
                hidden_states = hidden_states.reshape(batch_size, height, width, -1).permute(0, 3, 1, 2).contiguous()
        hidden_states = self.layer_norm(hidden_states)
        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)
        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )