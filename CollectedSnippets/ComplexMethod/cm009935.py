def _run_chain(
    chain: Chain | Runnable,
    inputs: dict[str, Any],
    callbacks: Callbacks,
    *,
    tags: list[str] | None = None,
    input_mapper: Callable[[dict], Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict | str:
    """Run a chain on inputs."""
    inputs_ = inputs if input_mapper is None else input_mapper(inputs)
    if (
        isinstance(chain, Chain)
        and isinstance(inputs_, dict)
        and len(inputs_) == 1
        and chain.input_keys
    ):
        val = next(iter(inputs_.values()))
        output = chain.invoke(
            val,
            config=RunnableConfig(
                callbacks=callbacks,
                tags=tags or [],
                metadata=metadata or {},
            ),
        )
    else:
        runnable_config = RunnableConfig(
            tags=tags or [],
            callbacks=callbacks,
            metadata=metadata or {},
        )
        output = chain.invoke(inputs_, config=runnable_config)
    return output