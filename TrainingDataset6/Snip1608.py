def build_middleware_stack(self) -> ASGIApp:
        # Duplicate/override from Starlette to add AsyncExitStackMiddleware
        # inside of ExceptionMiddleware, inside of custom user middlewares
        debug = self.debug
        error_handler = None
        exception_handlers: dict[Any, ExceptionHandler] = {}

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]  # ty: ignore[invalid-argument-type]
            + self.user_middleware
            + [
                Middleware(
                    ExceptionMiddleware,  # ty: ignore[invalid-argument-type]
                    handlers=exception_handlers,
                    debug=debug,
                ),
                # Add FastAPI-specific AsyncExitStackMiddleware for closing files.
                # Before this was also used for closing dependencies with yield but
                # those now have their own AsyncExitStack, to properly support
                # streaming responses while keeping compatibility with the previous
                # versions (as of writing 0.117.1) that allowed doing
                # except HTTPException inside a dependency with yield.
                # This needs to happen after user middlewares because those create a
                # new contextvars context copy by using a new AnyIO task group.
                # This AsyncExitStack preserves the context for contextvars, not
                # strictly necessary for closing files but it was one of the original
                # intentions.
                # If the AsyncExitStack lived outside of the custom middlewares and
                # contextvars were set, for example in a dependency with 'yield'
                # in that internal contextvars context, the values would not be
                # available in the outer context of the AsyncExitStack.
                # By placing the middleware and the AsyncExitStack here, inside all
                # user middlewares, the same context is used.
                # This is currently not needed, only for closing files, but used to be
                # important when dependencies with yield were closed here.
                Middleware(AsyncExitStackMiddleware),  # ty: ignore[invalid-argument-type]
            ]
        )

        app = self.router
        for cls, args, kwargs in reversed(middleware):
            app = cls(app, *args, **kwargs)
        return app