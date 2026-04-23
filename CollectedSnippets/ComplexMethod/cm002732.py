def ForSequenceClassificationLoss(labels: torch.Tensor, pooled_logits: torch.Tensor, config, **kwargs) -> torch.Tensor:
    num_labels = config.num_labels
    if config.problem_type is None:
        if num_labels == 1:
            config.problem_type = "regression"
        elif num_labels > 1 and (labels.dtype in (torch.long, torch.int)):
            config.problem_type = "single_label_classification"
        else:
            config.problem_type = "multi_label_classification"

    labels = labels.to(pooled_logits.device)
    if config.problem_type == "regression":
        loss_fct = MSELoss()
        if num_labels == 1:
            return loss_fct(pooled_logits.squeeze(), labels.squeeze())
        else:
            return loss_fct(pooled_logits, labels)
    if config.problem_type == "single_label_classification":
        return fixed_cross_entropy(pooled_logits.view(-1, num_labels), labels.view(-1), **kwargs)

    if config.problem_type == "multi_label_classification":
        loss_fct = BCEWithLogitsLoss()
        return loss_fct(pooled_logits, labels)

    raise RuntimeError(f"Invalid problem type: {config.problem_type}")