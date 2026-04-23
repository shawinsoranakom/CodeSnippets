def apply_with_spec_decode(
        self,
        logits: torch.Tensor,
        num_draft_tokens: list[int],
    ) -> torch.Tensor:
        """Spec-decode version of apply().
        Priority: ``min_tokens`` > ``stop_token_ids`` / EOS.
        Example: ``num_draft_tokens = [2, 3, 1]``
          → ``logits`` shape ``[6, V]``, ``cumsum = [0, 2, 5, 6]``
          → request 0 owns rows 0‑1, request 1 rows 2‑4, request 2 row 5.
        """
        if not self.min_toks:
            return logits

        num_draft_arr = np.array(num_draft_tokens, dtype=np.int64)
        cumsum = np.concatenate([[0], np.cumsum(num_draft_arr)])

        entries = [
            (req_idx, min_tok, len(out_tok_ids), list(stop_tok_ids))
            for req_idx, (min_tok, out_tok_ids, stop_tok_ids) in self.min_toks.items()
            if stop_tok_ids
        ]

        if not entries:
            return logits

        all_rows: list[np.ndarray] = []  # row indices to mask
        all_toks: list[np.ndarray] = []  # stop-token ids at those rows

        for req_idx, min_tok, current_len, stop_toks in entries:
            remaining = min_tok - current_len
            # How many leading draft positions still need stop-token masking.
            n_mask = int(min(max(remaining, 0), num_draft_arr[req_idx]))

            if n_mask > 0:
                offset = cumsum[req_idx]
                row_indices = np.arange(offset, offset + n_mask, dtype=np.int64)
                n_stop = len(stop_toks)
                all_rows.append(np.repeat(row_indices, n_stop))
                all_toks.append(np.tile(stop_toks, n_mask))

        if all_rows:
            rows_arr = np.concatenate(all_rows)
            toks_arr = np.concatenate(all_toks)
            # (row_indices, token_indices) for index_put_ to set -inf.
            logits_slice = (
                torch.from_numpy(rows_arr).to(self.device, non_blocking=True),
                torch.from_numpy(toks_arr).to(self.device, non_blocking=True),
            )
            logits.index_put_(logits_slice, self.neg_inf_tensor)

        return logits