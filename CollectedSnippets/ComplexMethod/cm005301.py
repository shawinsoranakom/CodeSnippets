def decoder_query(self, inputs, modality_sizes=None, inputs_without_pos=None, subsampled_points=None):
        if self.position_encoding_type == "none":  # Queries come from elsewhere
            raise ValueError("You cannot construct decoder queries when position_encoding_type is set to none")
        if subsampled_points is not None:
            # subsampled_points are the indices if the inputs would be flattened
            # however, the inputs aren't flattened, that's why we use unravel_index
            # to get the indices for the unflattened array
            # unravel_index returns a tuple (x_idx, y_idx, ...)
            # stack to get the [n, d] tensor of coordinates
            indices = torch.unravel_index(subsampled_points, self.output_index_dims)
            pos = torch.stack(indices, dim=1)
            batch_size = inputs.shape[0]
            # Map these coordinates to [-1, 1]
            pos = -1 + 2 * pos / torch.tensor(self.output_index_dims)[None, :]
            pos = torch.broadcast_to(pos[None], [batch_size, pos.shape[0], pos.shape[1]])
            # Construct the position encoding.
            if self.position_encoding_type == "trainable":
                pos_emb = self.output_position_encodings(batch_size)
            elif self.position_encoding_type == "fourier":
                pos_emb = self.output_position_encodings(
                    self.output_index_dims, batch_size=batch_size, device=inputs.device, dtype=inputs.dtype, pos=pos
                )

            # Optionally project them to a target dimension.
            pos_emb = self.positions_projection(pos_emb)
            pos_emb = torch.reshape(pos_emb, [pos_emb.shape[0], -1, pos_emb.shape[-1]])
        else:
            batch_size = inputs.shape[0]
            index_dims = inputs.shape[2:]

            # Construct the position encoding.
            if self.position_encoding_type == "trainable":
                pos_emb = self.output_position_encodings(batch_size)
            elif self.position_encoding_type == "fourier":
                pos_emb = self.output_position_encodings(
                    index_dims, batch_size, device=inputs.device, dtype=inputs.dtype
                )

            # Optionally project them to a target dimension.
            pos_emb = self.positions_projection(pos_emb)

        if self.concat_preprocessed_input:
            if inputs_without_pos is None:
                raise ValueError("Value is required for inputs_without_pos if concat_preprocessed_input is True")
            pos_emb = torch.cat([inputs_without_pos, pos_emb], dim=-1)

        return pos_emb