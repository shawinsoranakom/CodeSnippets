def sample_token(self, logits, temperature, top_k, top_p, min_p, repetition_penalty, token_history, generator, do_sample=True, presence_penalty=0.0):

        if not do_sample or temperature == 0.0:
            return torch.argmax(logits, dim=-1, keepdim=True)

        # Sampling mode
        if repetition_penalty != 1.0:
            for i in range(logits.shape[0]):
                for token_id in set(token_history):
                    logits[i, token_id] *= repetition_penalty if logits[i, token_id] < 0 else 1/repetition_penalty

        if presence_penalty is not None and presence_penalty != 0.0:
            for i in range(logits.shape[0]):
                for token_id in set(token_history):
                    logits[i, token_id] -= presence_penalty

        if temperature != 1.0:
            logits = logits / temperature

        if top_k > 0:
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = torch.finfo(logits.dtype).min

        if min_p > 0.0:
            probs_before_filter = torch.nn.functional.softmax(logits, dim=-1)
            top_probs, _ = probs_before_filter.max(dim=-1, keepdim=True)
            min_threshold = min_p * top_probs
            indices_to_remove = probs_before_filter < min_threshold
            logits[indices_to_remove] = torch.finfo(logits.dtype).min

        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(torch.nn.functional.softmax(sorted_logits, dim=-1), dim=-1)
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 0] = False
            indices_to_remove = torch.zeros_like(logits, dtype=torch.bool)
            indices_to_remove.scatter_(1, sorted_indices, sorted_indices_to_remove)
            logits[indices_to_remove] = torch.finfo(logits.dtype).min

        probs = torch.nn.functional.softmax(logits, dim=-1)

        return torch.multinomial(probs, num_samples=1, generator=generator)