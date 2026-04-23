def _build_network_inputs(
        self, inputs: torch.Tensor, network_input_is_1d: bool = True, interpolate_pos_encoding: bool = False
    ):
        """
        Construct the final input, including position encoding.

        This method expects the inputs to always have channels as last dimension.

        """
        batch_size = inputs.shape[0]
        input_size = inputs.shape[1:3]
        index_dims = inputs.shape[1:-1]
        indices = np.prod(index_dims)

        # Flatten input features to a 1D index dimension if necessary.
        if len(inputs.shape) > 3 and network_input_is_1d:
            inputs = torch.reshape(inputs, [batch_size, indices, -1])

        # Construct the position encoding.
        if self.position_encoding_type == "trainable":
            pos_enc = self.position_embeddings(batch_size, interpolate_pos_encoding, input_size)
        elif self.position_encoding_type == "fourier":
            pos_enc = self.position_embeddings(index_dims, batch_size, device=inputs.device, dtype=inputs.dtype)

        # Optionally project them to a target dimension.
        pos_enc = self.positions_projection(pos_enc)

        if not network_input_is_1d:
            # Reshape pos to match the input feature shape
            # if the network takes non-1D inputs
            sh = inputs.shape
            pos_enc = torch.reshape(pos_enc, list(sh)[:-1] + [-1])
        if self.concat_or_add_pos == "concat":
            inputs_with_pos = torch.cat([inputs, pos_enc], dim=-1)
        elif self.concat_or_add_pos == "add":
            inputs_with_pos = inputs + pos_enc
        return inputs_with_pos, inputs