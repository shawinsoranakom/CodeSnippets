def _predict_with_sentence_dedup(
        self, model_input: Dict[str, Any], texts: List[str]
    ) -> Tuple[List[str], List[float]]:
        if len(texts) <= 1:
            return self._predict(model_input=model_input)

        grouped_indices: Dict[str, List[int]] = {}
        for idx, text in enumerate(texts):
            grouped_indices.setdefault(text, []).append(idx)

        if all(len(indices) == 1 for indices in grouped_indices.values()):
            return self._predict(model_input=model_input)

        preds: List[str] = [""] * len(texts)
        confidences: List[float] = [0.0] * len(texts)
        for indices in grouped_indices.values():
            group_input = {name: value[indices] for name, value in model_input.items()}
            if len(indices) > 1:
                for name in ("input_ids", "token_type_ids", "attention_masks"):
                    group_input[name] = group_input[name][:1]

            group_preds, group_confidences = self._predict(model_input=group_input)
            for output_idx, pred, confidence in zip(indices, group_preds, group_confidences):
                preds[output_idx] = pred
                confidences[output_idx] = confidence

        return preds, confidences