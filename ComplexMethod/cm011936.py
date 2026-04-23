def _cancel_all_tasks(
    loop: AbstractEventLoop,
    tasks: OrderedSet[Future],  # type: ignore[type-arg]
) -> None:
    to_cancel = [task for task in tasks if not task.done()]

    if not to_cancel:
        return

    # pyre-fixme[1001]: Awaitable assigned to `task` is never awaited.
    for task in to_cancel:
        task.cancel()

    # pyrefly: ignore [bad-argument-type]
    loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during asyncio.run() shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )