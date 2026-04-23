def cross_attention(
        self,
        query_states,
        protein_key_value_states,
        structure_key_value_states,
        msa_key_value_states,
        query_attn_mask,
        protein_kv_attn_mask,
        structure_kv_attn_mask,
        msa_kv_attn_mask,
    ):
        """
        query_states: text
        key_value_states: protein
        query_states: [bs, query_seq_len, dim]
        key_value_states: [bs, kv_seq_len, dim]
        query_attn_mask: [bs, query_seq_len]
        kv_attn_mask: [bs, kv_seq_len]
        """

        # Concatenate protein and structure
        kv_attn_mask = [protein_kv_attn_mask, structure_kv_attn_mask, msa_kv_attn_mask]
        kv_attn_mask = [_ for _ in kv_attn_mask if _ is not None]
        if not kv_attn_mask:
            raise ValueError("At least one modality should be provided for cross attention.")
        kv_attn_mask = torch.cat(kv_attn_mask, dim=1)

        query_layer = self.attention_norm(query_states)

        # Warning: This place might cause issues, refers to
        # https://discuss.pytorch.org/t/cuda-error-cublas-status-not-supported-when-calling-cublasltmatmul-from-torch-nn-functional-linear/170214/13
        # Solution: add `DISABLE_ADDMM_CUDA_LT=1` as environment variable
        # Apply linear transformation to input_query, input_key, and input_value
        query_layer = self.query(query_layer)  # [bs, querylength, dim]

        if self.key_protein is not None and self.value_protein is not None:
            protein_key_value_states = protein_key_value_states.to(query_states)
            key_layer_protein = self.key_protein(protein_key_value_states)  # [bs, keylength, dim]
            value_layer_protein = self.value_protein(protein_key_value_states)  # [bs, keylength, dim]
        else:
            key_layer_protein = None
            value_layer_protein = None

        if self.key_structure is not None and self.value_structure is not None:
            structure_key_value_states = structure_key_value_states.to(query_states)
            key_layer_structure = self.key_structure(structure_key_value_states)  # [bs, keylength, dim]
            value_layer_structure = self.value_structure(structure_key_value_states)  # [bs, keylength, dim]
        else:
            key_layer_structure = None
            value_layer_structure = None

        if self.key_msa is not None and self.value_msa is not None:
            msa_key_value_states = msa_key_value_states.to(query_states)
            key_layer_msa = self.key_msa(msa_key_value_states)  # [bs, keylength, dim]
            value_layer_msa = self.value_msa(msa_key_value_states)  # [bs, keylength, dim]
        else:
            key_layer_msa = None
            value_layer_msa = None

        key_layer = [key_layer_protein, key_layer_structure, key_layer_msa]
        key_layer = [_ for _ in key_layer if _ is not None]
        key_layer = torch.cat(key_layer, dim=1)

        value_layer = [value_layer_protein, value_layer_structure, value_layer_msa]
        value_layer = [_ for _ in value_layer if _ is not None]
        value_layer = torch.cat(value_layer, dim=1)

        new_query_layer_shape = query_layer.size()[:-1] + (
            self.num_attention_heads,
            self.attention_head_size,
        )
        query_layer = query_layer.view(*new_query_layer_shape).permute(0, 2, 1, 3)

        new_key_layer_shape = key_layer.size()[:-1] + (
            self.num_attention_heads,
            self.attention_head_size,
        )
        key_layer = key_layer.view(*new_key_layer_shape).permute(0, 2, 1, 3)

        new_value_layer_shape = value_layer.size()[:-1] + (
            self.num_attention_heads,
            self.attention_head_size,
        )
        value_layer = value_layer.view(*new_value_layer_shape).permute(0, 2, 1, 3)

        query_layer = query_layer * self.scale

        # attention_mask: [bs, 1, querylength, keylength]
        if query_attn_mask is None:
            query_attn_mask = torch.ones(query_states.size(0), query_states.size(1)).to(query_states.device)
        attention_mask = query_attn_mask[:, None, :, None] * kv_attn_mask[:, None, None, :]
        # Compute the scaled dot-product attention scores
        attn_weights = torch.matmul(query_layer, key_layer.transpose(-1, -2))  # [bs, numheads, querylength, keylength]
        attn_weights = attn_weights - attn_weights.amax(dim=-1, keepdim=True).detach()  # To stabilize score
        attention_scores = attn_weights.masked_fill(
            (1 - attention_mask).bool(), torch.finfo(attn_weights.dtype).min
        )  # [bs, numheads, querylength, keylength]

        attention_probs = nn.Softmax(dim=-1)(attention_scores)

        # attention_probs_dropped = self.dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value_layer)  # [bs, numheads, querylength, dim/numheads]

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        context_layer = self.out_proj(context_layer)

        return context_layer