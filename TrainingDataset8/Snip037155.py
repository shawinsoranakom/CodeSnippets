async def async_context_mgr():
        try:
            yield
        finally:
            pass