def test_json_equality_evaluator_evaluate_lists_permutation_invariant() -> None:
    evaluator = JsonEqualityEvaluator()
    prediction = '[{"a": 1, "b": 2}, {"a": 2, "b": 3}]'
    reference = '[{"a": 2, "b": 3}, {"a": 1, "b": 2}]'
    result = evaluator.evaluate_strings(prediction=prediction, reference=reference)
    assert result == {"score": True}

    prediction = '[{"a": 1, "b": 2}, {"a": 2, "b": 3}]'
    reference = '[{"a": 2, "b": 3}, {"a": 1, "b": 4}]'
    result = evaluator.evaluate_strings(prediction=prediction, reference=reference)
    assert result == {"score": False}

    prediction = '[{"a": 1, "b": 2}, {"a": 2, "b": 3}]'
    reference = '[{"a": 2, "b": 3}]'
    result = evaluator.evaluate_strings(prediction=prediction, reference=reference)
    assert result == {"score": False}

    prediction = '[{"a": 1, "b": 2}, {"a": 2, "b": 3}]'
    reference = '[{"a": 2, "b": 3}, {"a": 1, "b": 2}, {"a": 3, "b": 4}]'
    result = evaluator.evaluate_strings(prediction=prediction, reference=reference)
    assert result == {"score": False}

    prediction = '[{"a": 1, "b": 2}, {"a": 2, "b": 3}]'
    reference = '[{"a": 2, "b": 3}, {"b": 2,"a": 1}, {"a": 3, "b": 4}]'
    result = evaluator.evaluate_strings(prediction=reference, reference=prediction)
    assert result == {"score": False}

    # Limit tests
    prediction = (
        "[" + ",".join([f'{{"a": {i}, "b": {i + 1}}}' for i in range(1000)]) + "]"
    )
    rlist = [f'{{"a": {i}, "b": {i + 1}}}' for i in range(1000)]
    random.shuffle(rlist)
    reference = "[" + ",".join(rlist) + "]"
    result = evaluator.evaluate_strings(prediction=prediction, reference=reference)
    assert result == {"score": True}

    prediction = (
        "[" + ",".join([f'{{"b": {i + 1}, "a": {i}}}' for i in range(1000)]) + "]"
    )
    reference = (
        "["
        + ",".join(
            [f'{{"a": {i + 1}, "b": {i + 2}}}' for i in range(999)]
            + ['{"a": 1000, "b": 1001}'],
        )
        + "]"
    )
    result = evaluator.evaluate_strings(prediction=prediction, reference=reference)
    assert result == {"score": False}