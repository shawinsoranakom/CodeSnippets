async def _shutdown(self) -> None:
        """
        Run any `.on_shutdown` event handlers.

        This method is kept for backward compatibility after Starlette removed
        support for on_startup/on_shutdown handlers.

        Ref: https://github.com/Kludex/starlette/pull/3117
        """
        for handler in self.on_shutdown:
            if is_async_callable(handler):
                await handler()
            else:
                handler()