def __call__(
                self, input_ids: torch.LongTensor, scores: torch.FloatTensor
            ) -> torch.FloatTensor:
                if self.penalty_last_n == 0 or self.penalty == 1.0:
                    return scores
                batch_size, seq_len = input_ids.shape
                vocab_size = scores.shape[-1]
                for b in range(batch_size):
                    start_index = max(0, seq_len - self.penalty_last_n)
                    window_indices = input_ids[b, start_index:]
                    if window_indices.numel() == 0:
                        continue
                    for token_id in set(window_indices.tolist()):
                        if token_id >= vocab_size:
                            continue
                        logit = scores[b, token_id]
                        scores[b, token_id] = (
                            logit * self.penalty if logit <= 0 else logit / self.penalty
                        )
                return scores