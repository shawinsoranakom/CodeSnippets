def check_exception(exc: BaseException) -> bool:
        if isinstance(exc, WebSocketDisconnect):
            return True

        exc_name = type(exc).__name__
        exc_str = str(exc)

        if "WebSocketDisconnect" in exc_name or "NO_STATUS_RCVD" in exc_str:
            return True

        # Recursively check ExceptionGroup
        if hasattr(exc, "exceptions") and getattr(exc, "exceptions", None):
            exceptions_list = getattr(exc, "exceptions", [])
            for sub_exc in exceptions_list:
                if check_exception(sub_exc):
                    return True

        # Check chained exceptions
        if hasattr(exc, "__cause__") and exc.__cause__:
            if check_exception(exc.__cause__):
                return True

        # Check context exceptions
        if hasattr(exc, "__context__") and exc.__context__:
            if check_exception(exc.__context__):
                return True

        return False