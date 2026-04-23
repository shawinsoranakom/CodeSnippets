def __init__(
        self,
        func: Callable[[Input], Iterator[Output]]
        | Callable[[Input], Runnable[Input, Output]]
        | Callable[[Input], Output]
        | Callable[[Input, RunnableConfig], Output]
        | Callable[[Input, CallbackManagerForChainRun], Output]
        | Callable[[Input, CallbackManagerForChainRun, RunnableConfig], Output]
        | Callable[[Input], Awaitable[Output]]
        | Callable[[Input], AsyncIterator[Output]]
        | Callable[[Input, RunnableConfig], Awaitable[Output]]
        | Callable[[Input, AsyncCallbackManagerForChainRun], Awaitable[Output]]
        | Callable[
            [Input, AsyncCallbackManagerForChainRun, RunnableConfig], Awaitable[Output]
        ],
        afunc: Callable[[Input], Awaitable[Output]]
        | Callable[[Input], AsyncIterator[Output]]
        | Callable[[Input, RunnableConfig], Awaitable[Output]]
        | Callable[[Input, AsyncCallbackManagerForChainRun], Awaitable[Output]]
        | Callable[
            [Input, AsyncCallbackManagerForChainRun, RunnableConfig], Awaitable[Output]
        ]
        | None = None,
        name: str | None = None,
    ) -> None:
        """Create a `RunnableLambda` from a callable, and async callable or both.

        Accepts both sync and async variants to allow providing efficient
        implementations for sync and async execution.

        Args:
            func: Either sync or async callable
            afunc: An async callable that takes an input and returns an output.

            name: The name of the `Runnable`.

        Raises:
            TypeError: If the `func` is not a callable type.
            TypeError: If both `func` and `afunc` are provided.

        """
        if afunc is not None:
            self.afunc = afunc
            func_for_name: Callable = afunc

        if is_async_callable(func) or is_async_generator(func):
            if afunc is not None:
                msg = (
                    "Func was provided as a coroutine function, but afunc was "
                    "also provided. If providing both, func should be a regular "
                    "function to avoid ambiguity."
                )
                raise TypeError(msg)
            self.afunc = func
            func_for_name = func
        elif callable(func):
            self.func = cast("Callable[[Input], Output]", func)
            func_for_name = func
        else:
            msg = (
                "Expected a callable type for `func`."
                f"Instead got an unsupported type: {type(func)}"
            )
            raise TypeError(msg)

        try:
            if name is not None:
                self.name = name
            elif func_for_name.__name__ != "<lambda>":
                self.name = func_for_name.__name__
        except AttributeError:
            pass

        self._repr: str | None = None