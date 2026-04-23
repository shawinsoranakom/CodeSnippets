async def amake_requests(
    urls: str | list[str],
    response_callback: (
        Callable[[ClientResponse, ClientSession], Awaitable[dict | list[dict]]] | None
    ) = None,
    **kwargs,
):
    """Make multiple requests asynchronously.

    Parameters
    ----------
    urls : Union[str, list[str]]
        list of urls to make requests to
    method : Literal["GET", "POST"], optional
        HTTP method to use.  Can be "GET" or "POST", by default "GET"
    timeout : int, optional
        Timeout in seconds, by default 10.  Can be overwritten by user setting, request_timeout
    response_callback : Callable[[ClientResponse, ClientSession], Awaitable[Union[dict, list[dict]]]], optional
        Async callback with response and session as arguments that returns the json, by default None
    session : ClientSession, optional
        Custom session to use for requests, by default None

    Returns
    -------
    Union[dict, list[dict]]
        Response json
    """
    session = kwargs.pop("session", await get_async_requests_session(**kwargs))
    ret_exceptions = kwargs.pop("return_exceptions", False)
    kwargs["response_callback"] = response_callback
    urls = urls if isinstance(urls, list) else [urls]

    try:
        results: list = []
        exceptions: list = []

        for result in await asyncio.gather(
            *[amake_request(url, session=session, **kwargs) for url in urls],
            return_exceptions=True,
        ):
            is_exception = isinstance(result, Exception)

            if is_exception and (
                isinstance(result, UnauthorizedError)
                or kwargs.get("raise_for_status", False)
            ):
                raise result  # type: ignore[misc]

            if is_exception and ret_exceptions:
                results.append(result)  # type: ignore[arg-type]
                continue

            if is_exception:
                exceptions.append(result)  # type: ignore[arg-type]
                continue

            if not result:
                continue

            if not isinstance(result, Exception):
                results.extend(result if isinstance(result, list) else [result])  # type: ignore[list-item]

        if exceptions and not results and not ret_exceptions:
            raise exceptions[0]  # type: ignore

        return results

    finally:
        await session.close()