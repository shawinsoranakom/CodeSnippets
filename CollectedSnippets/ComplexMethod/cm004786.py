def forward(self, pixel_values, output_hidden_states=False, return_dict=True):
        all_hidden_states = () if output_hidden_states else None

        hidden_states = pixel_values
        for idx, layers in enumerate(zip(self.patch_embeddings, self.block)):
            embedding_layer, block_layer = layers
            # Get patch embeddings from hidden_states
            hidden_states = embedding_layer(hidden_states)
            # Send the embeddings through the blocks
            for _, blk in enumerate(block_layer):
                layer_outputs = blk(hidden_states)
                hidden_states = layer_outputs[0]

            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states] if v is not None)

        return BaseModelOutputWithNoAttention(last_hidden_state=hidden_states, hidden_states=all_hidden_states)