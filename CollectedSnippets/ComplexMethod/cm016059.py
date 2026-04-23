def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: torch.Tensor | None = None,
        bias_k: torch.Tensor | None = None,
        bias_v: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        r"""Uses a scaled dot product with the projected key-value pair to update
        the projected query.
        Args:
            query (Tensor): Projected query
            key (Tensor): Projected key
            value (Tensor): Projected value
            attn_mask (BoolTensor, optional): 3D mask that prevents attention to certain positions.
            bias_k and bias_v: (Tensor, optional): one more key and value sequence to be added at
                sequence dim (dim=-3). Those are used for incremental decoding. Users should provide
                non-None to both arguments in order to activate them.
        Shape:
            - query: :math:`(L, N * H, E / H)`
            - key: :math:`(S, N * H, E / H)`
            - value: :math:`(S, N * H, E / H)`
            - attn_mask: :math:`(N * H, L, S)`, positions with ``True`` are not allowed to attend
                while ``False`` values will be unchanged.
            - bias_k and bias_v:bias: :math:`(1, N * H, E / H)`
            - Output: :math:`(L, N * H, E / H)`, :math:`(N * H, L, S)`
            where L is the target length, S is the source length, H is the number
            of attention heads, N is the batch size, and E is the embedding dimension.
        """
        if bias_k is not None and bias_v is not None:
            if not (
                key.size(-1) == bias_k.size(-1)
                and key.size(-2) == bias_k.size(-2)
                and bias_k.size(-3) == 1
            ):
                raise AssertionError(
                    f"Shape of bias_k is not supported: key.shape={key.shape}, bias_k.shape={bias_k.shape}"
                )
            if not (
                value.size(-1) == bias_v.size(-1)
                and value.size(-2) == bias_v.size(-2)
                and bias_v.size(-3) == 1
            ):
                raise AssertionError(
                    f"Shape of bias_v is not supported: value.shape={value.shape}, bias_v.shape={bias_v.shape}"
                )
            key = torch.cat([key, bias_k])
            value = torch.cat([value, bias_v])
            if attn_mask is not None:
                _attn_mask = attn_mask
                attn_mask = torch.nn.functional.pad(_attn_mask, [0, 1])

        tgt_len, head_dim = query.size(-3), query.size(-1)
        if not (query.size(-1) == key.size(-1) == value.size(-1)):
            raise AssertionError(
                f"The feature dim of query, key, value must be equal: "
                f"query={query.size(-1)}, key={key.size(-1)}, value={value.size(-1)}"
            )
        if key.size() != value.size():
            raise AssertionError(
                f"Shape of key, value must match: key.shape={key.shape}, value.shape={value.shape}"
            )
        src_len = key.size(-3)
        batch_heads = max(query.size(-2), key.size(-2))

        # Scale query
        query, key, value = (
            query.transpose(-2, -3),
            key.transpose(-2, -3),
            value.transpose(-2, -3),
        )
        query = query * (float(head_dim) ** -0.5)
        if attn_mask is not None:
            if attn_mask.dim() != 3:
                raise RuntimeError("attn_mask must be a 3D tensor.")
            if (
                (attn_mask.size(-1) != src_len)
                or (attn_mask.size(-2) != tgt_len)
                or (attn_mask.size(-3) != 1 and attn_mask.size(-3) != batch_heads)
            ):
                raise RuntimeError("The size of the attn_mask is not correct.")
            if attn_mask.dtype != torch.bool:
                raise RuntimeError("Only bool tensor is supported for attn_mask")

        # Dot product of q, k
        attn_output_weights = torch.matmul(query, key.mT)
        if attn_mask is not None:
            attn_output_weights.masked_fill_(
                attn_mask,
                -1e8,
            )
        attn_output_weights = torch.nn.functional.softmax(attn_output_weights, dim=-1)
        attn_output_weights = torch.nn.functional.dropout(
            attn_output_weights, p=self.dropout, training=self.training
        )
        attn_output = torch.matmul(attn_output_weights, value)
        return attn_output.transpose(-2, -3), attn_output_weights