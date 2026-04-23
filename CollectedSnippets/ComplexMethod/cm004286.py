def forward(
        self,
        query_states,
        protein_kv_states,
        structure_kv_states,
        msa_kv_states,
        query_attn_mask,
        protein_kv_attn_mask=None,
        structure_kv_attn_mask=None,
        msa_kv_attn_mask=None,
        protein_batch_mask=None,
        structure_batch_mask=None,
        msa_batch_mask=None,
        past_key_values=None,
    ):
        if protein_kv_states is not None:
            bs, protein_kv_seq_len, dim = protein_kv_states.shape
            if protein_kv_attn_mask is None:
                protein_kv_attn_mask = (
                    torch.ones(bs, protein_kv_seq_len).to(protein_batch_mask.device)
                    * protein_batch_mask.expand(size=(protein_kv_seq_len, bs)).T
                ).to(protein_kv_states.device)
        else:
            protein_kv_attn_mask = None

        if structure_kv_states is not None:
            bs, structure_kv_seq_len, dim = structure_kv_states.shape
            if structure_kv_attn_mask is None:
                structure_kv_attn_mask = (
                    torch.ones(bs, structure_kv_seq_len).to(protein_batch_mask.device)
                    * structure_batch_mask.expand(size=(structure_kv_seq_len, bs)).T
                ).to(structure_kv_states.device)
        else:
            structure_kv_attn_mask = None

        if msa_kv_states is not None:
            bs, msa_kv_seq_len, dim = msa_kv_states.shape
            if msa_kv_attn_mask is None:
                msa_kv_attn_mask = (
                    torch.ones(bs, msa_kv_seq_len).to(protein_batch_mask.device)
                    * msa_batch_mask.expand(size=(msa_kv_seq_len, bs)).T
                ).to(msa_kv_states.device)
        else:
            msa_kv_attn_mask = None
        hidden_states = query_states
        # only when there's at least one valid modality, crossattention will be performed
        if (
            (protein_kv_states is not None and protein_kv_attn_mask.any())
            or (structure_kv_states is not None and structure_kv_attn_mask.any())
            or (msa_kv_states is not None and msa_kv_attn_mask.any())
        ):
            residual = hidden_states
            hidden_states = self.cross_attention(
                query_states=hidden_states,
                protein_key_value_states=protein_kv_states,
                structure_key_value_states=structure_kv_states,
                msa_key_value_states=msa_kv_states,
                query_attn_mask=query_attn_mask,
                protein_kv_attn_mask=protein_kv_attn_mask,
                structure_kv_attn_mask=structure_kv_attn_mask,
                msa_kv_attn_mask=msa_kv_attn_mask,
            )  # [bs, query_seq_len, dim]
            # tanh gate
            hidden_states = torch.tanh(self.gate_attention) * hidden_states

            hidden_states = residual + hidden_states  # input_query

            residual = hidden_states
            hidden_states = self.ff(hidden_states) * torch.tanh(self.gate_ffw)
            hidden_states = residual + hidden_states

        return hidden_states