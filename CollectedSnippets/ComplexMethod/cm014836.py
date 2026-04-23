def convert_flash_attn_S_to_softmax(
        self,
        S,
        seqlen_q,
        seqlen_k,
        query_padding_mask,
        key_padding_mask,
        causal=False,
        window_size=(-1, -1),  # -1 means infinite window size
    ):
        """FlashAttention stores the S matrix in a different way.
        Arguments:
            S: (batch_size, nheads, seqlen_q, seqlen_k)
            query_padding_mask: (batch_size, seqlen_q)
            key_padding_mask: (batch_size, seqlen_k)
        """
        if TEST_WITH_ROCM:
            return S
        b = S.shape[0]

        if causal:
            window_size = (window_size[0], 0)
        seqlen_q_rounded, seqlen_k_rounded = S.shape[-2:]
        S_converted = S
        if window_size[0] >= 0 or window_size[1] >= 0:
            local_mask = self.construct_local_mask(
                seqlen_q,
                seqlen_k,
                window_size,
                query_padding_mask,
                key_padding_mask,
                S.device,
            )
            local_mask = F.pad(
                local_mask,
                (0, seqlen_k_rounded - seqlen_k, 0, seqlen_q_rounded - seqlen_q),
                value=True,
            )
            S_converted = S_converted.masked_fill(local_mask, 0.0)

        # Need to zero out things not in attention_mask in case S was initialized with random values
        # and some of those values aren't overwritten.
        seqlen_q_og = (
            query_padding_mask.shape[-1] if query_padding_mask is not None else seqlen_q_rounded
        )
        if query_padding_mask is not None:
            query_padding_mask = F.pad(query_padding_mask, (0, seqlen_q_rounded - seqlen_q_og))
            # S_converted = S_converted.masked_fill(rearrange(~query_padding_mask, "b s -> b 1 s 1"), 0.0)
            S_converted = S_converted.masked_fill(~query_padding_mask.view(b, 1, -1, 1), 0.0)
        seqlen_k_og = key_padding_mask.shape[-1] if key_padding_mask is not None else seqlen_k
        if key_padding_mask is not None:
            key_padding_mask = F.pad(key_padding_mask, (0, seqlen_k_rounded - seqlen_k_og))
            S_converted = S_converted.masked_fill(~key_padding_mask.view(b, 1, 1, -1), 0.0)
            # S_converted = S_converted.masked_fill(rearrange(~key_padding_mask, "b s -> b 1 1 s"), 0.0)
        S_converted = F.pad(S_converted, (0, 0, 0, seqlen_q_og - seqlen_q_rounded))
        S_converted = F.pad(S_converted, (0, seqlen_k_og - seqlen_k_rounded))
        return S_converted[:, :, :seqlen_q, :seqlen_k]