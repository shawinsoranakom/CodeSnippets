def test_parallel_sampling(vllm_model, example_prompts) -> None:
    """Test passes if parallel sampling `n>1` yields `n` unique completions.

    Args:
      vllm_model: VllmRunner instance under test.
      example_prompt: test fixture providing prompts for testing.
    """
    sampling_params_list, n_list = _get_test_sampling_params(example_prompts)
    llm: LLM = vllm_model.llm
    outputs = llm.generate(example_prompts, sampling_params_list)

    # Validate each request response
    for out, n in zip(outputs, n_list):
        completion_counts: dict[str, int] = {}
        # Assert correct number of completions
        assert len(out.outputs) == n, f"{len(out.outputs)} completions; {n} expected."
        for idx in range(n):
            comp = out.outputs[idx]
            # Assert correct completion indices
            assert comp.index == idx, f"Index {comp.index}; expected {idx}."
            text = comp.text
            completion_counts[text] = completion_counts.get(text, 0) + 1
        # Assert unique completions
        if len(completion_counts) != n:
            repeats = {txt: num for (txt, num) in completion_counts.items() if num > 1}
            raise AssertionError(
                f"{len(completion_counts)} unique completions; expected"
                f" {n}. Repeats: {repeats}"
            )