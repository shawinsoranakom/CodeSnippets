def test_end_text_if_open_emits_text_end_before_finish_step():
    """StreamTextEnd must be emitted before StreamFinishStep during compaction.

    When ``emit_end_if_ready`` fires compaction events while a text block is
    still open, ``_end_text_if_open`` must close it first.  If StreamFinishStep
    arrives before StreamTextEnd, the Vercel AI SDK clears ``activeTextParts``
    and raises "Received text-end for missing text part".
    """
    adapter = _adapter()

    # Open a text block by processing an AssistantMessage with text
    msg = AssistantMessage(content=[TextBlock(text="partial response")], model="test")
    adapter.convert_message(msg)
    assert adapter.has_started_text
    assert not adapter.has_ended_text

    # Simulate what service.py does before yielding compaction events
    pre_close: list[StreamBaseResponse] = []
    adapter._end_text_if_open(pre_close)
    combined = pre_close + list(compaction_events("Compacted transcript"))

    text_end_idx = next(
        (i for i, e in enumerate(combined) if isinstance(e, StreamTextEnd)), None
    )
    finish_step_idx = next(
        (i for i, e in enumerate(combined) if isinstance(e, StreamFinishStep)), None
    )

    assert text_end_idx is not None, "StreamTextEnd must be present"
    assert finish_step_idx is not None, "StreamFinishStep must be present"
    assert text_end_idx < finish_step_idx, (
        f"StreamTextEnd (idx={text_end_idx}) must precede "
        f"StreamFinishStep (idx={finish_step_idx}) — otherwise the Vercel AI SDK "
        "clears activeTextParts before text-end arrives"
    )