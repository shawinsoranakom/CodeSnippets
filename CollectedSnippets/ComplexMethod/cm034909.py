def beam_search(self, x, beam_width, eos, embed):
        def _inflate(tensor, times, dim):
            repeat_dims = [1] * tensor.dim()
            repeat_dims[dim] = times
            output = paddle.tile(tensor, repeat_dims)
            return output

        # https://github.com/IBM/pytorch-seq2seq/blob/fede87655ddce6c94b38886089e05321dc9802af/seq2seq/models/TopKDecoder.py
        batch_size, l, d = x.shape
        x = paddle.tile(
            paddle.transpose(x.unsqueeze(1), perm=[1, 0, 2, 3]), [beam_width, 1, 1, 1]
        )
        inflated_encoder_feats = paddle.reshape(
            paddle.transpose(x, perm=[1, 0, 2, 3]), [-1, l, d]
        )

        # Initialize the decoder
        state = self.decoder.get_initial_state(embed, tile_times=beam_width)

        pos_index = paddle.reshape(
            paddle.arange(batch_size) * beam_width, shape=[-1, 1]
        )

        # Initialize the scores
        sequence_scores = paddle.full(
            shape=[batch_size * beam_width, 1], fill_value=-float("Inf")
        )
        index = [i * beam_width for i in range(0, batch_size)]
        sequence_scores[index] = 0.0

        # Initialize the input vector
        y_prev = paddle.full(
            shape=[batch_size * beam_width], fill_value=self.num_classes
        )

        # Store decisions for backtracking
        stored_scores = list()
        stored_predecessors = list()
        stored_emitted_symbols = list()

        for i in range(self.max_len_labels):
            output, state = self.decoder(inflated_encoder_feats, state, y_prev)
            state = paddle.unsqueeze(state, axis=0)
            log_softmax_output = paddle.nn.functional.log_softmax(output, axis=1)

            sequence_scores = _inflate(sequence_scores, self.num_classes, 1)
            sequence_scores += log_softmax_output
            scores, candidates = paddle.topk(
                paddle.reshape(sequence_scores, [batch_size, -1]), beam_width, axis=1
            )

            # Reshape input = (bk, 1) and sequence_scores = (bk, 1)
            y_prev = paddle.reshape(
                candidates % self.num_classes, shape=[batch_size * beam_width]
            )
            sequence_scores = paddle.reshape(scores, shape=[batch_size * beam_width, 1])

            # Update fields for next timestep
            pos_index = paddle.expand_as(pos_index, candidates)
            predecessors = paddle.cast(
                candidates / self.num_classes + pos_index, dtype="int64"
            )
            predecessors = paddle.reshape(
                predecessors, shape=[batch_size * beam_width, 1]
            )
            state = paddle.index_select(state, index=predecessors.squeeze(), axis=1)

            # Update sequence scores and erase scores for <eos> symbol so that they aren't expanded
            stored_scores.append(sequence_scores.clone())
            y_prev = paddle.reshape(y_prev, shape=[-1, 1])
            eos_prev = paddle.full_like(y_prev, fill_value=eos)
            mask = eos_prev == y_prev
            mask = paddle.nonzero(mask)
            if mask.dim() > 0:
                sequence_scores = sequence_scores.numpy()
                mask = mask.numpy()
                sequence_scores[mask] = -float("inf")
                sequence_scores = paddle.to_tensor(sequence_scores)

            # Cache results for backtracking
            stored_predecessors.append(predecessors)
            y_prev = paddle.squeeze(y_prev)
            stored_emitted_symbols.append(y_prev)

        # Do backtracking to return the optimal values
        # ====== backtrak ======#
        # Initialize return variables given different types
        p = list()
        l = [
            [self.max_len_labels] * beam_width for _ in range(batch_size)
        ]  # Placeholder for lengths of top-k sequences

        # the last step output of the beams are not sorted
        # thus they are sorted here
        sorted_score, sorted_idx = paddle.topk(
            paddle.reshape(stored_scores[-1], shape=[batch_size, beam_width]),
            beam_width,
        )

        # initialize the sequence scores with the sorted last step beam scores
        s = sorted_score.clone()

        batch_eos_found = [0] * batch_size  # the number of EOS found
        # in the backward loop below for each batch
        t = self.max_len_labels - 1
        # initialize the back pointer with the sorted order of the last step beams.
        # add pos_index for indexing variable with b*k as the first dimension.
        t_predecessors = paddle.reshape(
            sorted_idx + pos_index.expand_as(sorted_idx),
            shape=[batch_size * beam_width],
        )
        while t >= 0:
            # Re-order the variables with the back pointer
            current_symbol = paddle.index_select(
                stored_emitted_symbols[t], index=t_predecessors, axis=0
            )
            t_predecessors = paddle.index_select(
                stored_predecessors[t].squeeze(), index=t_predecessors, axis=0
            )
            eos_indices = stored_emitted_symbols[t] == eos
            eos_indices = paddle.nonzero(eos_indices)

            if eos_indices.dim() > 0:
                for i in range(eos_indices.shape[0] - 1, -1, -1):
                    # Indices of the EOS symbol for both variables
                    # with b*k as the first dimension, and b, k for
                    # the first two dimensions
                    idx = eos_indices[i]
                    b_idx = int(idx[0] / beam_width)
                    # The indices of the replacing position
                    # according to the replacement strategy noted above
                    res_k_idx = beam_width - (batch_eos_found[b_idx] % beam_width) - 1
                    batch_eos_found[b_idx] += 1
                    res_idx = b_idx * beam_width + res_k_idx

                    # Replace the old information in return variables
                    # with the new ended sequence information
                    t_predecessors[res_idx] = stored_predecessors[t][idx[0]]
                    current_symbol[res_idx] = stored_emitted_symbols[t][idx[0]]
                    s[b_idx, res_k_idx] = stored_scores[t][idx[0], 0]
                    l[b_idx][res_k_idx] = t + 1

            # record the back tracked results
            p.append(current_symbol)
            t -= 1

        # Sort and re-order again as the added ended sequences may change
        # the order (very unlikely)
        s, re_sorted_idx = s.topk(beam_width)
        for b_idx in range(batch_size):
            l[b_idx] = [l[b_idx][k_idx.item()] for k_idx in re_sorted_idx[b_idx, :]]

        re_sorted_idx = paddle.reshape(
            re_sorted_idx + pos_index.expand_as(re_sorted_idx),
            [batch_size * beam_width],
        )

        # Reverse the sequences and re-order at the same time
        # It is reversed because the backtracking happens in reverse time order
        p = [
            paddle.reshape(
                paddle.index_select(step, re_sorted_idx, 0),
                shape=[batch_size, beam_width, -1],
            )
            for step in reversed(p)
        ]
        p = paddle.concat(p, -1)[:, 0, :]
        return p, paddle.ones_like(p)