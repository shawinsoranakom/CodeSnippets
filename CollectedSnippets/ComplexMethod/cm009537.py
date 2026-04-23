def __init__(
        self,
        *steps: RunnableLike,
        name: str | None = None,
        first: Runnable[Any, Any] | None = None,
        middle: list[Runnable[Any, Any]] | None = None,
        last: Runnable[Any, Any] | None = None,
    ) -> None:
        """Create a new `RunnableSequence`.

        Args:
            steps: The steps to include in the sequence.
            name: The name of the `Runnable`.
            first: The first `Runnable` in the sequence.
            middle: The middle `Runnable` objects in the sequence.
            last: The last `Runnable` in the sequence.

        Raises:
            ValueError: If the sequence has less than 2 steps.
        """
        steps_flat: list[Runnable] = []
        if not steps and first is not None and last is not None:
            steps_flat = [first] + (middle or []) + [last]
        for step in steps:
            if isinstance(step, RunnableSequence):
                steps_flat.extend(step.steps)
            else:
                steps_flat.append(coerce_to_runnable(step))
        if len(steps_flat) < _RUNNABLE_SEQUENCE_MIN_STEPS:
            msg = (
                f"RunnableSequence must have at least {_RUNNABLE_SEQUENCE_MIN_STEPS} "
                f"steps, got {len(steps_flat)}"
            )
            raise ValueError(msg)
        super().__init__(
            first=steps_flat[0],
            middle=list(steps_flat[1:-1]),
            last=steps_flat[-1],
            name=name,
        )