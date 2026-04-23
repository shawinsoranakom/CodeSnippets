def forward(
        self,
        hidden_states: torch.Tensor,
        pooling_metadata: PoolingMetadata,
    ) -> SequencePoolerOutput:
        lens_tensor = pooling_metadata.prompt_lens
        lens: list[int] = lens_tensor.tolist()
        B: int = len(lens)

        prompt_token_ids = pooling_metadata.get_prompt_token_ids_cpu()
        offset = 0
        pooled_list: list[torch.Tensor] = []

        for i in range(B):
            L = int(lens[i])
            hs = hidden_states[offset : offset + L]
            token_ids = prompt_token_ids[i]

            start_idx = 0
            end_idx = L
            if self.remove_cls_sep:
                if (
                    self.cls_token_id is not None
                    and int(token_ids[0]) == self.cls_token_id
                ):
                    start_idx = 1
                if (
                    self.sep_token_id is not None
                    and int(token_ids[L - 1]) == self.sep_token_id
                ):
                    end_idx = max(start_idx, L - 1)

            if end_idx <= start_idx:
                V = int(self.mlm_head.decoder.out_features)
                pooled_list.append(hs.new_zeros((V,)))
                offset += L
                continue

            logits_i = self.mlm_head(hs[start_idx:end_idx])
            scores_i = torch.log1p(torch.relu(logits_i))

            if self.pooling == "sum":
                pooled_i = scores_i.sum(dim=0)
            else:  # "max"
                pooled_i = scores_i.max(dim=0).values

            pooled_list.append(pooled_i.contiguous())
            offset += L

        return torch.stack(pooled_list, dim=0).contiguous()