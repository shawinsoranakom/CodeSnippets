def _prepare_false_positive_mitigations(
    op: Callable[..., Any],
    sample: SampleInput,
    tensors: list[tuple[str, torch.Tensor]],
) -> _FalsePositiveMitigations:
    """Create negated and non-rounded sample variants for false positive detection."""
    m = _FalsePositiveMitigations()

    try:
        m.negated_sample = create_fully_negated_sample(sample)
        m.negated_tensors = negate_all_tensors(tensors)
        result = _run_op_on_sample(op, m.negated_sample)
        if _is_tensor_output(result):
            m.negated_ground_truth = _to_ground_truth(result)
        else:
            m.negated_sample = None
    except Exception:
        m.negated_sample = None
        m.negated_tensors = None

    if "rounding_mode" not in sample.kwargs:
        return m

    try:
        non_rounded_kwargs = {
            k: v for k, v in sample.kwargs.items() if k != "rounding_mode"
        }
        m.non_rounded_sample = SampleInput(
            sample.input, args=sample.args, kwargs=non_rounded_kwargs
        )
        result = _run_op_on_sample(op, m.non_rounded_sample)
        if not _is_tensor_output(result):
            m.non_rounded_sample = None
        else:
            m.non_rounded_ground_truth = _to_ground_truth(result)
            m.non_rounded_negated_sample = create_fully_negated_sample(
                m.non_rounded_sample
            )
            m.non_rounded_negated_tensors = negate_all_tensors(tensors)
            nr_neg_result = _run_op_on_sample(op, m.non_rounded_negated_sample)
            if _is_tensor_output(nr_neg_result):
                m.non_rounded_negated_ground_truth = _to_ground_truth(nr_neg_result)
            else:
                m.non_rounded_negated_sample = None
    except Exception:
        m.non_rounded_sample = None
        m.non_rounded_ground_truth = None
        m.non_rounded_negated_sample = None

    return m