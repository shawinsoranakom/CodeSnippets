async def get_flow_events_response(
    *,
    job_id: str,
    queue_service: JobQueueService,
    event_delivery: EventDeliveryType,
):
    """Get events for a specific build job, either as a stream or single event."""
    try:
        main_queue, event_manager, event_task, _ = queue_service.get_queue_data(job_id)
        if event_delivery in (EventDeliveryType.STREAMING, EventDeliveryType.DIRECT):
            if event_task is None:
                await logger.aerror(f"No event task found for job {job_id}")
                raise HTTPException(status_code=404, detail="No event task found for job")
            return await create_flow_response(
                queue=main_queue,
                event_manager=event_manager,
                event_task=event_task,
            )

        # Polling mode - get all available events
        try:
            events: list = []
            # Get all available events from the queue without blocking
            while not main_queue.empty():
                _, value, _ = await main_queue.get()
                if value is None:
                    # End of stream, trigger end event
                    if event_task is not None:
                        event_task.cancel()
                    event_manager.on_end(data={})
                    # Include the end event
                    events.append(None)
                    break
                events.append(value.decode("utf-8"))

            # If no events were available, wait for one (with timeout)
            if not events:
                _, value, _ = await main_queue.get()
                if value is None:
                    # End of stream, trigger end event
                    if event_task is not None:
                        event_task.cancel()
                    event_manager.on_end(data={})
                else:
                    events.append(value.decode("utf-8"))

            # Return as NDJSON format - each line is a complete JSON object
            content = "\n".join([event for event in events if event is not None])
            return Response(content=content, media_type="application/x-ndjson")
        except asyncio.CancelledError as exc:
            await logger.ainfo(f"Event polling was cancelled for job {job_id}")
            raise HTTPException(status_code=499, detail="Event polling was cancelled") from exc
        except asyncio.TimeoutError:
            await logger.awarning(f"Timeout while waiting for events for job {job_id}")
            return Response(content="", media_type="application/x-ndjson")  # Return empty response instead of error

    except JobQueueNotFoundError as exc:
        await logger.aerror(f"Job not found: {job_id}. Error: {exc!s}")
        raise HTTPException(status_code=404, detail=f"Job not found: {exc!s}") from exc
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        await logger.aexception(f"Unexpected error processing flow events for job {job_id}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc!s}") from exc