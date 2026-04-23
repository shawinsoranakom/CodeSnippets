def wrapper(app: Any) -> _AsyncLiftContextManager[Any]:
        return _AsyncLiftContextManager(cmgr(app))