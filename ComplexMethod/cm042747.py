def _maybeDeferred_coro(
    f: Callable[_P, Any], warn: bool, *args: _P.args, **kw: _P.kwargs
) -> Deferred[Any]:
    """Copy of defer.maybeDeferred that also converts coroutines to Deferreds."""
    try:
        result = f(*args, **kw)
    except:  # noqa: E722
        return fail(failure.Failure(captureVars=Deferred.debug))

    # when the deprecation period has ended we need to make sure the behavior
    # of the public maybeDeferred_coro() function isn't changed, or drop it in
    # the same release
    if isinstance(result, Deferred):
        if warn:
            warnings.warn(
                f"{global_object_name(f)} returned a Deferred, this is deprecated."
                f" Please refactor this function to return a coroutine.",
                ScrapyDeprecationWarning,
                stacklevel=2,
            )
        return result
    if asyncio.isfuture(result) or inspect.isawaitable(result):
        return deferred_from_coro(result)
    if isinstance(result, failure.Failure):  # pragma: no cover
        if warn:
            warnings.warn(
                f"{global_object_name(f)} returned a Failure, this is deprecated."
                f" Please refactor this function to return a coroutine.",
                ScrapyDeprecationWarning,
                stacklevel=2,
            )
        return fail(result)
    return succeed(result)