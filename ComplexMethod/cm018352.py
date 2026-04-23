def create_reasoning_item(
    id: str,
    output_index: int,
    reasoning_summary: list[list[str]] | list[str] | str | None = None,
) -> list[ResponseStreamEvent]:
    """Create a reasoning item."""

    if reasoning_summary is None:
        reasoning_summary = [[]]
    elif isinstance(reasoning_summary, str):
        reasoning_summary = [reasoning_summary]
    if isinstance(reasoning_summary, list) and all(
        isinstance(item, str) for item in reasoning_summary
    ):
        reasoning_summary = [reasoning_summary]

    events = [
        ResponseOutputItemAddedEvent(
            item=ResponseReasoningItem(
                id=id,
                summary=[],
                type="reasoning",
                status=None,
                encrypted_content="AAA",
            ),
            output_index=output_index,
            sequence_number=0,
            type="response.output_item.added",
        )
    ]

    for summary_index, summary in enumerate(reasoning_summary):
        events.append(
            ResponseReasoningSummaryPartAddedEvent(
                item_id=id,
                output_index=output_index,
                part={"text": "", "type": "summary_text"},
                sequence_number=0,
                summary_index=summary_index,
                type="response.reasoning_summary_part.added",
            )
        )
        events.extend(
            ResponseReasoningSummaryTextDeltaEvent(
                delta=delta,
                item_id=id,
                output_index=output_index,
                sequence_number=0,
                summary_index=summary_index,
                type="response.reasoning_summary_text.delta",
            )
            for delta in summary
        )
        events.extend(
            [
                ResponseReasoningSummaryTextDoneEvent(
                    item_id=id,
                    output_index=output_index,
                    sequence_number=0,
                    summary_index=summary_index,
                    text="".join(summary),
                    type="response.reasoning_summary_text.done",
                ),
                ResponseReasoningSummaryPartDoneEvent(
                    item_id=id,
                    output_index=output_index,
                    part={"text": "".join(summary), "type": "summary_text"},
                    sequence_number=0,
                    summary_index=summary_index,
                    type="response.reasoning_summary_part.done",
                ),
            ]
        )

    events.append(
        ResponseOutputItemDoneEvent(
            item=ResponseReasoningItem(
                id=id,
                summary=[
                    Summary(text="".join(summary), type="summary_text")
                    for summary in reasoning_summary
                ],
                type="reasoning",
                status=None,
                encrypted_content="AAABBB",
            ),
            output_index=output_index,
            sequence_number=0,
            type="response.output_item.done",
        ),
    )

    return events