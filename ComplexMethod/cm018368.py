async def mock_generator(events, **kwargs):
        if isinstance(events, Exception):
            raise events
        response = Response(
            id="resp_A",
            created_at=1700000000,
            error=None,
            incomplete_details=None,
            instructions=kwargs.get("instructions"),
            metadata=kwargs.get("metadata", {}),
            model=kwargs.get("model", "gpt-4o-mini"),
            object="response",
            output=[],
            parallel_tool_calls=kwargs.get("parallel_tool_calls", True),
            temperature=kwargs.get("temperature", 1.0),
            tool_choice=kwargs.get("tool_choice", "auto"),
            tools=kwargs.get("tools", []),
            top_p=kwargs.get("top_p", 1.0),
            max_output_tokens=kwargs.get("max_output_tokens", 100000),
            previous_response_id=kwargs.get("previous_response_id"),
            reasoning=kwargs.get("reasoning"),
            status="in_progress",
            text=kwargs.get(
                "text", ResponseTextConfig(format=ResponseFormatText(type="text"))
            ),
            truncation=kwargs.get("truncation", "disabled"),
            usage=None,
            user=kwargs.get("user"),
            store=kwargs.get("store", True),
        )
        yield ResponseCreatedEvent(
            response=response,
            sequence_number=0,
            type="response.created",
        )
        yield ResponseInProgressEvent(
            response=response,
            sequence_number=1,
            type="response.in_progress",
        )
        sequence_number = 2
        response.status = "completed"

        for value in events:
            if isinstance(value, ResponseOutputItemDoneEvent):
                response.output.append(value.item)
            elif isinstance(value, IncompleteDetails):
                response.status = "incomplete"
                response.incomplete_details = value
                break
            if isinstance(value, ResponseError):
                response.status = "failed"
                response.error = value
                break

            value.sequence_number = sequence_number
            sequence_number += 1
            yield value

            if isinstance(value, ResponseErrorEvent):
                return

        if response.status == "incomplete":
            yield ResponseIncompleteEvent(
                response=response,
                sequence_number=sequence_number,
                type="response.incomplete",
            )
        elif response.status == "failed":
            yield ResponseFailedEvent(
                response=response,
                sequence_number=sequence_number,
                type="response.failed",
            )
        else:
            yield ResponseCompletedEvent(
                response=response,
                sequence_number=sequence_number,
                type="response.completed",
            )