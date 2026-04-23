def _extract_token_timestamps(
        self, generate_outputs, alignment_heads, time_precision=0.02, num_frames=None, num_input_ids=None
    ):
        """
        Calculates token-level timestamps using the encoder-decoder cross-attentions and dynamic time-warping (DTW) to
        map each output token to a position in the input audio. If `num_frames` is specified, the encoder-decoder
        cross-attentions will be cropped before applying DTW.

        Returns:
            tensor containing the timestamps in seconds for each predicted token
        """
        # Create a list with `decoder_layers` elements, each a tensor of shape
        # (batch size * num beams, attention_heads, output length, input length).
        cross_attentions = []
        for i in range(self.config.decoder_layers):
            cross_attentions.append(torch.cat([x[i] for x in generate_outputs.cross_attentions], dim=2))

        # Select specific cross-attention layers and heads. This is a tensor
        # of shape (batch size * num beams, num selected heads, output length, input length).
        weights = torch.stack([cross_attentions[l][:, h] for l, h in alignment_heads])
        weights = weights.permute([1, 0, 2, 3])

        weight_length = None

        if "beam_indices" in generate_outputs:
            # If beam search was used, the sequence length of the outputs may not be the real sequence length:
            # beam search may end up returning a sequence that finished a few steps earlier while decoding.
            # In that case, the `cross_attentions` weights are too long and we have to make sure that they have
            # the right `output_length`

            # get the real sequence length of the longest sequence, crop the beam_indices to the real length
            weight_length = (generate_outputs.beam_indices != -1).sum(-1).max()
            beam_indices = generate_outputs.beam_indices[:, :weight_length]

            # The first forward pass (prefill) may have processed more than one token and, therefore, contain
            # cross-attention weights for several tokens.
            # Let's unroll the first `beam_indices` accordingly, so we can use it to gather the weights.
            if num_input_ids is not None and num_input_ids > 1:
                # `-1`: `beam_indices` can be used as-is to gather the weights when `num_input_ids` is 1
                weight_length += num_input_ids - 1
                beam_indices_first_step_unrolled = (
                    torch.ones(beam_indices.shape[0], num_input_ids - 1, device=beam_indices.device, dtype=torch.long)
                    * (beam_indices[:, 0:1])
                )
                unrolled_beam_indices = torch.cat([beam_indices_first_step_unrolled, beam_indices], dim=-1)
            else:
                unrolled_beam_indices = beam_indices

            # If beam index is still -1, it means that the associated token id is EOS
            # We need to replace the index with 0 since index_select gives an error if any of the indexes is -1.
            unrolled_beam_indices = unrolled_beam_indices.masked_fill(unrolled_beam_indices == -1, 0)

            # Select the cross attention from the right beam for each output sequence, up to the real sequence
            # length (`weight_length`)
            weights = torch.stack(
                [
                    torch.index_select(weights[:, :, i, :], dim=0, index=unrolled_beam_indices[:, i])
                    for i in range(unrolled_beam_indices.shape[1])
                ],
                dim=2,
            )

        # make sure timestamps are as long as weights
        input_length = weight_length or cross_attentions[0].shape[2]
        batch_size = generate_outputs.sequences.shape[0]
        timestamps = torch.zeros(
            (batch_size, input_length + 1), dtype=torch.float32, device=generate_outputs.sequences.device
        )

        if num_frames is not None:
            # two cases:
            # 1. num_frames is the same for each sample -> compute the DTW matrix for each sample in parallel
            # 2. num_frames is different, compute the DTW matrix for each sample sequentially

            # we're using np.unique because num_frames can be int/list/tuple
            if isinstance(num_frames, int):
                weights = weights[..., : num_frames // 2]

            elif isinstance(num_frames, (list, tuple, np.ndarray)) and len(np.unique(num_frames)) == 1:
                weights = weights[..., : num_frames[0] // 2]

            elif isinstance(num_frames, (torch.Tensor)) and len(torch.unique(num_frames)) == 1:
                weights = weights[..., : num_frames[0] // 2]

            else:
                # num_frames is of shape (batch_size,) whereas batch_size is truly batch_size*num_return_sequences
                repeat_time = batch_size if isinstance(num_frames, int) else batch_size // len(num_frames)
                num_frames = num_frames.cpu() if isinstance(num_frames, (torch.Tensor)) else num_frames
                num_frames = np.repeat(num_frames, repeat_time)

        # let's ignore decoder_input_ids that can negatively impact the DTW while we know they have timestamps 0.0s
        # (they are not taken into account for the DTW in OAI implementation)
        if num_input_ids is not None:
            weights = weights[:, :, num_input_ids:, :]

        # Since we ignore `decoder_input_ids` in the DTW and in the case where we generated only one token (for which we don't have cross attentions, see below comments),
        # the DTW sequence length is 0 and we should return only 0.0s for the token timestamps
        if weights.shape[2] == 0:
            return timestamps

        if num_frames is None or isinstance(num_frames, int):
            # Normalize and smoothen the weights.
            std = torch.std(weights, dim=-2, keepdim=True, unbiased=False)
            mean = torch.mean(weights, dim=-2, keepdim=True)
            weights = (weights - mean) / std
            weights = _median_filter(weights, self.config.median_filter_width)

            # Average the different cross-attention heads.
            weights = weights.mean(dim=1)

        # Perform dynamic time warping on each element of the batch.
        for batch_idx in range(batch_size):
            if num_frames is not None and isinstance(num_frames, (tuple, list, np.ndarray, torch.Tensor)):
                matrix = weights[batch_idx, ..., : num_frames[batch_idx] // 2]

                # Normalize and smoothen the weights.
                std = torch.std(matrix, dim=-2, keepdim=True, unbiased=False)
                mean = torch.mean(matrix, dim=-2, keepdim=True)
                matrix = (matrix - mean) / std
                matrix = _median_filter(matrix, self.config.median_filter_width)

                # Average the different cross-attention heads.
                matrix = matrix.mean(dim=0)
            else:
                matrix = weights[batch_idx]

            text_indices, time_indices = _dynamic_time_warping(-matrix.cpu().double().numpy())
            jumps = np.pad(np.diff(text_indices), (1, 0), constant_values=1).astype(bool)
            jump_times = time_indices[jumps] * time_precision

            # each predicted token has a corresponding timestamp, expect the eos token (or last predicted token) for which we don't retrieve cross attentions
            # (indeed contrary to OAI that re-run a full forward to retrieve cross attentions for each token and therefore also the last one predicted, we retrieve
            # cross attentions directly from the auto-regressive generation, so we don't have cross attentiosn for the token at the end of the sequence. Nevertheless,
            # that is not important since we expect this last token to be the eos token)
            # 1. for decoder_input_ids, we set the timestamps to 0.0
            # 2. for the eos token (or last predicted token), we simply duplicate the timestamp of the last non-eos token
            timestamps[batch_idx] = torch.cat(
                [torch.zeros(num_input_ids), torch.tensor(jump_times), torch.tensor([jump_times[-1]])]
            )

        return timestamps