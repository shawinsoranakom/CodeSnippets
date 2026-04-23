async def async_multi_execute_lifx_with_retries(
    methods: list[Callable], attempts: int, overall_timeout: int
) -> list[Message]:
    """Execute multiple lifx callback methods with retries and wait for a response.

    This functional will the overall timeout by the number of attempts and
    wait for each method to return a result. If we don't get a result
    within the split timeout, we will send all methods that did not generate
    a response again.

    If we don't get a result after all attempts, we will raise an
    TimeoutError exception.
    """
    loop = asyncio.get_running_loop()
    futures: list[asyncio.Future] = [loop.create_future() for _ in methods]

    def _callback(
        bulb: Light, message: Message | None, future: asyncio.Future[Message]
    ) -> None:
        if message and not future.done():
            future.set_result(message)

    timeout_per_attempt = overall_timeout / attempts

    for _ in range(attempts):
        for idx, method in enumerate(methods):
            future = futures[idx]
            if not future.done():
                method(callb=partial(_callback, future=future))

        _, pending = await asyncio.wait(futures, timeout=timeout_per_attempt)
        if not pending:
            break

    results: list[Message] = []
    failed: list[str] = []
    for idx, future in enumerate(futures):
        if not future.done() or not (result := future.result()):
            method = methods[idx]
            failed.append(str(getattr(method, "__name__", method)))
        else:
            results.append(result)

    if failed:
        failed_methods = ", ".join(failed)
        raise TimeoutError(f"{failed_methods} timed out after {attempts} attempts")

    return results