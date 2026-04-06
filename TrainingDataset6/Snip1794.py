def add_event_handler(
        self,
        event_type: str,
        func: Callable[[], Any],
    ) -> None:
        """
        Add an event handler function for startup or shutdown.

        This method is kept for backward compatibility after Starlette removed
        support for on_startup/on_shutdown handlers.

        Ref: https://github.com/Kludex/starlette/pull/3117
        """
        assert event_type in ("startup", "shutdown")
        if event_type == "startup":
            self.on_startup.append(func)
        else:
            self.on_shutdown.append(func)