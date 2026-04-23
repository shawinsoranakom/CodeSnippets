def forward(
        self,
        hidden_states,
        attention_mask=None,
        num_hashes=None,
        buckets=None,
        past_buckets_states=None,
        use_cache=False,
        output_attentions=False,
        **kwargs,
    ):
        sequence_length = hidden_states.shape[1]
        batch_size = hidden_states.shape[0]

        # num hashes can optionally be overwritten by user
        num_hashes = num_hashes if num_hashes is not None else self.num_hashes

        # check if cache shall be used and that hidden states are already cached
        exists_cache = past_buckets_states is not None and len(past_buckets_states) > self.layer_idx
        if exists_cache:
            assert sequence_length == 1, (
                "At the moment, auto-regressive language generation is only possible one word at a time. Make sure"
                f" that input sequence length {sequence_length} equals 1, when `past_buckets_states` is passed."
            )

            # get query vector
            query_vectors = self.query_key(hidden_states)
            query_vectors = self._split_hidden_size_dim(
                query_vectors, self.num_attention_heads, self.attention_head_size
            )

            past_buckets = past_buckets_states.buckets_cache[self.layer_idx]
            past_states = past_buckets_states.states_cache[self.layer_idx]

            if past_buckets.numel() != 0:
                key_value_hidden_states, sorted_bucket_idx, buckets = self._get_relevant_hid_states_and_buckets(
                    query_vectors=query_vectors,
                    attention_mask=attention_mask,
                    num_hashes=num_hashes,
                    hidden_states=hidden_states,
                    past_states=past_states,
                    past_buckets=past_buckets,
                )

                query_key_vectors = self._query_per_attn_head(key_value_hidden_states)
                value_vectors = self._value_per_attn_head(key_value_hidden_states)

                # split key & value vectors by num hashes to apply
                # self attention on each separately
                query_key_vectors = self._split_seq_length_dim_to(
                    query_key_vectors,
                    num_hashes,
                    -1,
                    self.num_attention_heads,
                    self.attention_head_size,
                )
                value_vectors = self._split_seq_length_dim_to(
                    value_vectors,
                    num_hashes,
                    -1,
                    self.num_attention_heads,
                    self.attention_head_size,
                )
                # repeat query vectors across hash dimension
                query_vectors = query_vectors.unsqueeze(2).repeat(1, 1, num_hashes, 1, 1)
            else:
                key_value_hidden_states = torch.cat([past_states, hidden_states], dim=1)

                query_key_vectors = self.query_key(key_value_hidden_states)
                value_vectors = self.value(key_value_hidden_states)

        else:
            # project hidden_states to query_key and value
            query_vectors = None
            query_key_vectors = self.query_key(hidden_states)
            value_vectors = self.value(hidden_states)

        # if query key is not already split
        if not exists_cache or past_buckets.numel() == 0:
            query_key_vectors = self._split_hidden_size_dim(
                query_key_vectors, self.num_attention_heads, self.attention_head_size
            )
            value_vectors = self._split_hidden_size_dim(
                value_vectors, self.num_attention_heads, self.attention_head_size
            )

        # cache buckets for next incremental decoding
        if exists_cache and key_value_hidden_states.shape[1] >= self.chunk_length:
            buckets = self._hash_vectors(query_key_vectors, num_hashes, attention_mask)

        # free memory
        del hidden_states

        assert query_key_vectors.shape[-1] == self.attention_head_size, (
            f"last dim of query_key_vectors is {query_key_vectors.shape[-1]} but should be {self.attention_head_size}."
        )
        assert value_vectors.shape[-1] == self.attention_head_size, (
            f"last dim of value_vectors is {value_vectors.shape[-1]} but should be {self.attention_head_size}."
        )

        do_standard_self_attention = (sequence_length <= self.chunk_length) or (
            exists_cache and past_states is not None
        )
        # LSH attention only makes sense if chunked attention should be performed
        if not do_standard_self_attention:
            # set `num_buckets` on the fly, recommended way to do it
            if self.num_buckets is None:
                self._set_num_buckets(sequence_length)

            # use cached buckets for backprop only
            if buckets is None:
                # hash query key vectors into buckets
                buckets = self._hash_vectors(query_key_vectors, num_hashes, attention_mask)
            else:
                # make sure buckets has correct shape for LSH attention
                buckets = buckets.view(batch_size, self.num_attention_heads, num_hashes * sequence_length)

            assert int(buckets.shape[-1]) == num_hashes * sequence_length, (
                f"last dim of buckets is {buckets.shape[-1]}, but should be {num_hashes * sequence_length}"
            )

            sorted_bucket_idx, undo_sorted_bucket_idx = self._get_sorted_bucket_idx_and_undo_sorted_bucket_idx(
                sequence_length, buckets, num_hashes
            )

            # make sure bucket idx is not longer then sequence length
            sorted_bucket_idx_per_hash = sorted_bucket_idx % sequence_length

            # cluster query key value vectors according to hashed buckets
            query_key_vectors = self._gather_by_expansion(query_key_vectors, sorted_bucket_idx_per_hash, num_hashes)
            value_vectors = self._gather_by_expansion(value_vectors, sorted_bucket_idx_per_hash, num_hashes)
            query_key_vectors = self._split_seq_length_dim_to(
                query_key_vectors,
                -1,
                self.chunk_length,
                self.num_attention_heads,
                self.attention_head_size,
            )
            value_vectors = self._split_seq_length_dim_to(
                value_vectors,
                -1,
                self.chunk_length,
                self.num_attention_heads,
                self.attention_head_size,
            )

            if self.chunk_length is None:
                assert self.num_chunks_before == 0 and self.num_chunks_after == 0, (
                    "If `config.chunk_length` is `None`, make sure `config.num_chunks_after` and"
                    " `config.num_chunks_before` are set to 0."
                )
        elif exists_cache and past_buckets.numel() != 0:
            # use max sequence length
            sorted_bucket_idx_per_hash = sorted_bucket_idx
        else:
            # get sequence length indices
            sorted_bucket_idx_per_hash = torch.arange(sequence_length, device=query_key_vectors.device).repeat(
                batch_size, self.num_attention_heads, 1
            )

        # scale key vectors
        sqrt_num = np.sqrt(self.attention_head_size)
        key_vectors = self._len_and_dim_norm(query_key_vectors, sqrt_num)

        # set query_vectors to query key vectors if LSH self attention
        query_vectors = query_vectors if query_vectors is not None else query_key_vectors

        # free memory
        del query_key_vectors

        # get attention probs
        out_vectors, logits, attention_probs = self._attend(
            query_vectors=query_vectors,
            key_vectors=key_vectors,
            value_vectors=value_vectors,
            sorted_bucket_idx_per_hash=sorted_bucket_idx_per_hash,
            attention_mask=attention_mask,
            do_standard_self_attention=do_standard_self_attention,
            use_cache=exists_cache,
        )

        # free memory
        del key_vectors, value_vectors

        # re-order out_vectors and logits
        if not do_standard_self_attention:
            # sort clusters back to correct ordering
            out_vectors, logits = ReverseSort.apply(out_vectors, logits, sorted_bucket_idx, undo_sorted_bucket_idx)

        if not do_standard_self_attention or (exists_cache and past_buckets.numel() != 0):
            # sum up all hash rounds
            if num_hashes > 1:
                out_vectors = self._split_seq_length_dim_to(
                    out_vectors,
                    num_hashes,
                    sequence_length,
                    self.num_attention_heads,
                    self.attention_head_size,
                )
                logits = self._split_seq_length_dim_to(
                    logits,
                    num_hashes,
                    sequence_length,
                    self.num_attention_heads,
                    self.attention_head_size,
                ).unsqueeze(-1)

                probs_vectors = torch.exp(logits - torch.logsumexp(logits, dim=2, keepdim=True))
                out_vectors = torch.sum(out_vectors * probs_vectors, dim=2)
                # free memory
                del probs_vectors

            # free memory
            del logits

        assert out_vectors.shape == (
            batch_size,
            self.num_attention_heads,
            sequence_length,
            self.attention_head_size,
        ), (
            "out_vectors have be of shape `[batch_size, config.num_attention_heads, sequence_length,"
            " config.attention_head_size]`."
        )

        out_vectors = self._merge_hidden_size_dims(out_vectors, self.num_attention_heads, self.attention_head_size)

        if output_attentions is False:
            attention_probs = ()

        if buckets is not None:
            buckets = buckets.view(batch_size, self.num_attention_heads, num_hashes, -1)

        return LSHSelfAttentionOutput(hidden_states=out_vectors, attention_probs=attention_probs, buckets=buckets)