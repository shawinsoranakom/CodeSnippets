def forward(
        self,
        hidden_states,
        attention_mask=None,
        num_hashes=None,
        past_buckets_states=None,
        use_cache=False,
        orig_sequence_length=None,
        output_attentions=False,
        buckets=None,
        **kwargs,
    ):
        hidden_states = self.layer_norm(hidden_states)

        # use cached buckets for backprob if buckets not None for LSHSelfAttention
        self_attention_outputs = self.self_attention(
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            num_hashes=num_hashes,
            past_buckets_states=past_buckets_states,
            use_cache=use_cache,
            output_attentions=output_attentions,
            buckets=buckets,
        )

        # add buckets if necessary
        if hasattr(self_attention_outputs, "buckets"):
            buckets = self_attention_outputs.buckets
        else:
            buckets = None

        # cache hidden states for future use
        if use_cache and past_buckets_states is not None:
            # padded input should not be cached during prefill
            states = (
                hidden_states[:, :orig_sequence_length]
                if len(past_buckets_states.states_cache) <= self.layer_id
                else hidden_states
            )
            buckets = (
                buckets[:, :, :, :orig_sequence_length]
                if (
                    len(past_buckets_states.buckets_cache) <= self.layer_id
                    and buckets is not None
                    and orig_sequence_length > 1
                )
                else buckets
            )
            buckets, hidden_states = past_buckets_states.update(
                buckets, states[:, :orig_sequence_length], self.layer_id
            )

        # compute attention feed forward output
        attention_output = self.output(self_attention_outputs.hidden_states)

        return AttentionOutput(
            hidden_states=attention_output,
            attention_probs=self_attention_outputs.attention_probs,
            buckets=buckets,
        )