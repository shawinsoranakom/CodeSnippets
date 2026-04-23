def postprocess(self, model_outputs, function_to_apply=None, top_k=5):
        if function_to_apply is None:
            if self.model.config.problem_type == "multi_label_classification" or self.model.config.num_labels == 1:
                function_to_apply = ClassificationFunction.SIGMOID
            elif self.model.config.problem_type == "single_label_classification" or self.model.config.num_labels > 1:
                function_to_apply = ClassificationFunction.SOFTMAX
            elif hasattr(self.model.config, "function_to_apply") and function_to_apply is None:
                function_to_apply = self.model.config.function_to_apply
            else:
                function_to_apply = ClassificationFunction.NONE

        if top_k > self.model.config.num_labels:
            top_k = self.model.config.num_labels

        outputs = model_outputs["logits"][0]
        if outputs.dtype in (torch.bfloat16, torch.float16):
            outputs = outputs.to(torch.float32).numpy()
        else:
            outputs = outputs.numpy()

        if function_to_apply == ClassificationFunction.SIGMOID:
            scores = sigmoid(outputs)
        elif function_to_apply == ClassificationFunction.SOFTMAX:
            scores = softmax(outputs)
        elif function_to_apply == ClassificationFunction.NONE:
            scores = outputs
        else:
            raise ValueError(f"Unrecognized `function_to_apply` argument: {function_to_apply}")

        dict_scores = [
            {"label": self.model.config.id2label[i], "score": score.item()} for i, score in enumerate(scores)
        ]
        dict_scores.sort(key=lambda x: x["score"], reverse=True)
        if top_k is not None:
            dict_scores = dict_scores[:top_k]

        return dict_scores