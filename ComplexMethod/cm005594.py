def postprocess(self, model_outputs, multi_label=False):
        candidate_labels = [outputs["candidate_label"] for outputs in model_outputs]
        sequences = [outputs["sequence"] for outputs in model_outputs]
        logits = np.concatenate([output["logits"].float().numpy() for output in model_outputs])
        N = logits.shape[0]
        n = len(candidate_labels)
        num_sequences = N // n
        reshaped_outputs = logits.reshape((num_sequences, n, -1))

        if multi_label or len(candidate_labels) == 1:
            # softmax over the entailment vs. contradiction dim for each label independently
            entailment_id = self.entailment_id
            contradiction_id = -1 if entailment_id == 0 else 0
            entail_contr_logits = reshaped_outputs[..., [contradiction_id, entailment_id]]
            scores = np.exp(entail_contr_logits) / np.exp(entail_contr_logits).sum(-1, keepdims=True)
            scores = scores[..., 1]
        else:
            # softmax the "entailment" logits over all candidate labels
            entail_logits = reshaped_outputs[..., self.entailment_id]
            scores = np.exp(entail_logits) / np.exp(entail_logits).sum(-1, keepdims=True)

        top_inds = list(reversed(scores[0].argsort()))
        return {
            "sequence": sequences[0],
            "labels": [candidate_labels[i] for i in top_inds],
            "scores": scores[0, top_inds].tolist(),
        }