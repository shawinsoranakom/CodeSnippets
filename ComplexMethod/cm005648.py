def postprocess(self, model_outputs, top_k=5, target_ids=None):
        # Cap top_k if there are targets
        if target_ids is not None and target_ids.shape[0] < top_k:
            top_k = target_ids.shape[0]
        input_ids = model_outputs["input_ids"][0]
        outputs = model_outputs["logits"]

        masked_index = torch.nonzero(input_ids == self.tokenizer.mask_token_id, as_tuple=False).squeeze(-1)
        # Fill mask pipeline supports only one ${mask_token} per sample

        logits = outputs[0, masked_index, :]
        probs = logits.softmax(dim=-1)
        if target_ids is not None:
            probs = probs[..., target_ids]

        values, predictions = probs.topk(top_k)

        result = []
        single_mask = values.shape[0] == 1
        for i, (_values, _predictions) in enumerate(zip(values.tolist(), predictions.tolist())):
            row = []
            for v, p in zip(_values, _predictions):
                # Copy is important since we're going to modify this array in place
                tokens = input_ids.numpy().copy()
                if target_ids is not None:
                    p = target_ids[p].tolist()

                tokens[masked_index[i]] = p
                # Filter padding out:
                tokens = tokens[np.where(tokens != self.tokenizer.pad_token_id)]
                # Originally we skip special tokens to give readable output.
                # For multi masks though, the other [MASK] would be removed otherwise
                # making the output look odd, so we add them back
                sequence = self.tokenizer.decode(tokens, skip_special_tokens=single_mask)
                proposition = {"score": v, "token": p, "token_str": self.tokenizer.decode([p]), "sequence": sequence}
                row.append(proposition)
            result.append(row)
        if single_mask:
            return result[0]
        return result