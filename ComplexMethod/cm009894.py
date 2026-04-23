def run(
        self,
        *args: Any,
        callbacks: Callbacks = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Convenience method for executing chain.

        The main difference between this method and `Chain.__call__` is that this
        method expects inputs to be passed directly in as positional arguments or
        keyword arguments, whereas `Chain.__call__` expects a single input dictionary
        with all the inputs

        Args:
            *args: If the chain expects a single input, it can be passed in as the
                sole positional argument.
            callbacks: Callbacks to use for this chain run. These will be called in
                addition to callbacks passed to the chain during construction, but only
                these runtime callbacks will propagate to calls to other objects.
            tags: List of string tags to pass to all callbacks. These will be passed in
                addition to tags passed to the chain during construction, but only
                these runtime tags will propagate to calls to other objects.
            metadata: Optional metadata associated with the chain.
            **kwargs: If the chain expects multiple inputs, they can be passed in
                directly as keyword arguments.

        Returns:
            The chain output.

        Example:
            ```python
            # Suppose we have a single-input chain that takes a 'question' string:
            chain.run("What's the temperature in Boise, Idaho?")
            # -> "The temperature in Boise is..."

            # Suppose we have a multi-input chain that takes a 'question' string
            # and 'context' string:
            question = "What's the temperature in Boise, Idaho?"
            context = "Weather report for Boise, Idaho on 07/03/23..."
            chain.run(question=question, context=context)
            # -> "The temperature in Boise is..."
            ```
        """
        # Run at start to make sure this is possible/defined
        _output_key = self._run_output_key

        if args and not kwargs:
            if len(args) != 1:
                msg = "`run` supports only one positional argument."
                raise ValueError(msg)
            return self(args[0], callbacks=callbacks, tags=tags, metadata=metadata)[
                _output_key
            ]

        if kwargs and not args:
            return self(kwargs, callbacks=callbacks, tags=tags, metadata=metadata)[
                _output_key
            ]

        if not kwargs and not args:
            msg = (
                "`run` supported with either positional arguments or keyword arguments,"
                " but none were provided."
            )
            raise ValueError(msg)
        msg = (
            f"`run` supported with either positional arguments or keyword arguments"
            f" but not both. Got args: {args} and kwargs: {kwargs}."
        )
        raise ValueError(msg)