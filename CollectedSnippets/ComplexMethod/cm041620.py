def _check_plugin(
    plugin: "BasePlugin",
    tokenizer: "PreTrainedTokenizer",
    processor: "ProcessorMixin",
    expected_mm_messages: list[dict[str, str]] = MM_MESSAGES,
    expected_input_ids: list[int] = INPUT_IDS,
    expected_labels: list[int] = LABELS,
    expected_mm_inputs: dict[str, Any] = {},
    expected_no_mm_inputs: dict[str, Any] = {},
) -> None:
    if plugin.__class__.__name__ == "Qwen2OmniPlugin":  # test omni_messages
        assert plugin.process_messages(OMNI_MESSAGES, IMAGES, NO_VIDEOS, AUDIOS, processor) == expected_mm_messages
        assert plugin.process_token_ids(INPUT_IDS, LABELS, IMAGES, NO_VIDEOS, AUDIOS, tokenizer, processor) == (
            expected_input_ids,
            expected_labels,
        )
        _is_close(
            plugin.get_mm_inputs(IMAGES, NO_VIDEOS, AUDIOS, IMGLENS, NO_VIDLENS, AUDLENS, BATCH_IDS, processor),
            expected_mm_inputs,
        )
    elif plugin.__class__.__name__ == "Qwen3VLPlugin":  # only check replacement
        assert plugin.process_messages(VIDEO_MESSAGES, NO_IMAGES, VIDEOS, NO_AUDIOS, processor) == expected_mm_messages
    elif plugin.__class__.__name__ != "BasePlugin":  # test mm_messages
        assert plugin.process_messages(MM_MESSAGES, IMAGES, NO_VIDEOS, NO_AUDIOS, processor) == expected_mm_messages
        assert plugin.process_token_ids(INPUT_IDS, LABELS, IMAGES, NO_VIDEOS, NO_AUDIOS, tokenizer, processor) == (
            expected_input_ids,
            expected_labels,
        )
        _is_close(
            plugin.get_mm_inputs(IMAGES, NO_VIDEOS, NO_AUDIOS, IMGLENS, NO_VIDLENS, NO_AUDLENS, BATCH_IDS, processor),
            expected_mm_inputs,
        )

    # test text_messages
    assert plugin.process_messages(TEXT_MESSAGES, NO_IMAGES, NO_VIDEOS, NO_AUDIOS, processor) == TEXT_MESSAGES
    assert plugin.process_token_ids(INPUT_IDS, LABELS, NO_IMAGES, NO_VIDEOS, NO_AUDIOS, tokenizer, processor) == (
        INPUT_IDS,
        LABELS,
    )
    _is_close(
        plugin.get_mm_inputs(
            NO_IMAGES, NO_VIDEOS, NO_AUDIOS, NO_IMGLENS, NO_VIDLENS, NO_AUDLENS, BATCH_IDS, processor
        ),
        expected_no_mm_inputs,
    )