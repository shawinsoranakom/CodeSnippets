def test_mm_cache_stats(
    num_gpus_available,
    image_urls,
    mm_processor_cache_type,
    caplog_vllm,
):
    llm = LLM(
        model="llava-hf/llava-1.5-7b-hf",
        max_model_len=4096,
        max_num_seqs=5,
        enforce_eager=True,
        mm_processor_cache_type=mm_processor_cache_type,
        disable_log_stats=False,
        limit_mm_per_prompt={"image": 2},
    )

    llm.chat(_make_messages(image_urls[0]))
    assert _get_mm_cache_stats(llm.get_metrics()) == (1, 0)
    assert _get_mm_cache_log(llm, caplog_vllm) == pytest.approx(0.0)

    llm.chat(_make_messages(image_urls[1]))
    assert _get_mm_cache_stats(llm.get_metrics()) == (2, 0)
    assert _get_mm_cache_log(llm, caplog_vllm) == pytest.approx(0.0)

    llm.chat(_make_messages(image_urls[0]))
    assert _get_mm_cache_stats(llm.get_metrics()) == (3, 1)
    assert _get_mm_cache_log(llm, caplog_vllm) == pytest.approx(33.3)

    # NOTE: This only resets hit rate stats in CachingMetrics
    # The raw queries and hits counts remain unaffected
    llm.reset_mm_cache()

    llm.chat(_make_messages(image_urls[0]))
    assert _get_mm_cache_stats(llm.get_metrics()) == (4, 1)
    assert _get_mm_cache_log(llm, caplog_vllm) == pytest.approx(0.0)

    llm.chat(_make_messages(image_urls[1]))
    assert _get_mm_cache_stats(llm.get_metrics()) == (5, 1)
    assert _get_mm_cache_log(llm, caplog_vllm) == pytest.approx(0.0)